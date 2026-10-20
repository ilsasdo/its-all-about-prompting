#!/usr/bin/env python3
from pathlib import Path
import json
import sys
from typing import Optional

from utils import (
    llm_generate, print_user, print_system, print_error, print_assistant,
    print_debug, read_file, write_file, search_file,
)

# Load rules from filesystem
def load_rules(rules_dir_path: str = "./rules") -> list:
    rules_content = ["Follow these rules:"]
    rules_dir = Path(rules_dir_path)
    if rules_dir.exists():
        for rule_file in sorted(rules_dir.glob("*.txt")):
            content = rule_file.read_text().strip()
            if content:
                rules_content.append(content)
    
    if len(rules_content) > 1:
        full_rules = "\n".join(rules_content)
        return [{"role": "user", "content": full_rules}]
    return []

def serialize_history(history: list[dict[str, str]]) -> str:
    prompt = "<|begin_of_text|>"
    for message in history:
        prompt += (
            f"<|start_header_id|>{message['role']}<|end_header_id|>\n\n"
            f"{message['content']}<|eot_id|>"
        )
    return prompt + "<|start_header_id|>assistant<|end_header_id|>\n\n"


def parse_tool_call(assistant_response: str) -> Optional[dict]:
    """Parse one tool call from the assistant response, or return the response as text."""
    try:
        clean_response = assistant_response.strip()
        if "```json" in clean_response:
            clean_response = clean_response.split("```json")[1].split("```")[
                0].strip()
        elif "```" in clean_response:
            clean_response = clean_response.split("```")[1].split("```")[
                0].strip()

        data = json.loads(clean_response)
        if not isinstance(data, dict) or data.get("name") not in (
                "read_file", "write_file", "search_file"):
            return None
        return data
    except (json.JSONDecodeError, IndexError):
        return None


def call_tool(tool_call: dict) -> dict[str, str]:
    """Execute a parsed tool call and return its result as a chat message."""
    tool_name = tool_call["name"]
    parameters = tool_call.get("parameters", {})
    if not isinstance(parameters, dict):
        result = f"Error: Parameters for {tool_name} must be an object."
    else:
        print_debug(f"Tool call: {tool_name}({parameters})")
        if tool_name == "read_file":
            result = read_file(parameters.get("path"))
        elif tool_name == "write_file":
            result = write_file(parameters.get("path"), parameters.get("content"))
        else:
            result = search_file(parameters.get("path"), parameters.get("file_name"))
        print_debug(f"Tool result: {result}")
    return {"role": "ipython", "content": result}


tools_prompt = """You have access to the following tools: 'read_file', 'write_file' and 'search_file'.
You can ONLY USE ONE TOOL AT A TIME. If you need to use multiple tools, you must call them in separate responses.

1. 'read_file': Obtain the content of a file from disk.
   To use it, respond with a correct json: {"name": "read_file", "parameters": {"path": "FILE_PATH"}}

2. 'write_file': Write content to a file on disk. Only refer to files mentioned by the user or previously found by 'search_file'.
   To use it, respond with a correct json: {"name": "write_file", "parameters": {"path": "FILE_PATH", "content": "FILE_CONTENT"}}

3. 'search_file': search for a file on disk.
   To use it, respond with a correct json: {"name": "search_file", "parameters": {"path": "FILE_PATH", "file_name": "FILE_NAME"}}

When you need to use a tool, provide the required parameters in the JSON object and ANSWER ONLY with a single valid JSON string, example:
GOOD ANSWER: {"name": "search_file", "parameters": {"path": ".", "file_name": "my_file.txt"}}
BAD ANSWER: {"name": "search_file", "parameters": {"path": ".", "file_name": "my_file.txt"}}; {"name": "search_file", "parameters": {"path": ".", "file_name": "another_file.txt"}}

IMPORTANT: DO NOT COMBINE MULTIPLE TOOL CALLS IN A SINGLE RESPONSE.
IMPORTANT: INVOKE A SINGLE FUNCTION THEN WAIT FOR THE RESULT BEFORE CALLING ANOTHER FUNCTION.

If you are not calling a tool, do not use JSON format."""

def chat(debug=False):
    history = load_rules()
    history.append({"role": "user", "content": tools_prompt})
    
    print("Chat with LLM (type 'exit' or 'quit' to stop, '/plan' to generate a plan, '/summarize' to summarize chat)")

    plan_prompt = """Analyze the task and provide a detailed step-by-step plan for its execution.
    Identify potential risks, dependencies, and key milestones.
    Format the output as a numbered list with clear explanations for each step."""

    summarize_prompt = """Summarize the current chat history into a concise yet detailed summary.
Retain the most relevant information and current task context.
The summary will be used to reduce the context size, so it must capture the essence of the entire conversation."""

    while True:
        print_user("You: ", end="")
        user_input = input()
        if user_input.lower() in ['exit', 'quit']:
            break
            
        is_summarize = user_input.strip().lower() == '/summarize'
        if is_summarize:
            history.append({"role": "user", "content": summarize_prompt})
        else:
            if user_input.strip().lower().startswith('/plan'):
                history.append({"role": "user", "content": f"{plan_prompt}\n{user_input}"})
            else:
                # Append user input to history
                history.append({"role": "user", "content": user_input})
        
        try:
            assistant_response = llm_generate(serialize_history(history), raw=True, debug=debug)
            tool_call = parse_tool_call(assistant_response)

            print_system("Assistant: ", end="")
            print_assistant(tool_call)
            
            if is_summarize:
                # Replace history with the summary while keeping rules
                history = load_rules()
                history.append({"role": "assistant", "content": f"Summary of previous chat history:\n{tool_call}"})
            else:
                # Append assistant response to history
                history.append({"role": "tool", "content": tool_call})
            
        except Exception as e:
            print_error(f"Error: {e}")
            # Remove the last user message if it failed
            if history and history[-1]["role"] == "user":
                history.pop()

if __name__ == "__main__":
    debug = "--debug" in sys.argv
    chat(debug)
