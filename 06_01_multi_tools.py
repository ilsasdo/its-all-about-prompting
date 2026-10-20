#!/usr/bin/env python3
import json
import sys
from pathlib import Path
from typing import Optional

from utils import (
    llm_generate, print_user, print_system, print_error, print_assistant,
    print_debug, read_file, write_file, search_file,
)

# PROMPT: read file "my_custom_file.txt" and write its content to foo.bar.txt file
# SHOW: ollama show llama3.2 --template

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


def generate_response(history: list[dict[str, str]], debug: bool = False) -> str:
    """Generate a response, executing tool calls until the model responds normally."""
    # NOTE: We limit the number of consecutive tool calls to prevent infinite loops or excessive tool usage.
    MAX_CONSECUTIVE_TOOL_CALLS = 10
    tool_calls = 0

    # NOTE: A NESTED LOOP!
    while True:
        assistant_response = llm_generate(serialize_history(history), raw=True, debug=debug)
        history.append({"role": "assistant", "content": assistant_response})
        parsed_response = parse_tool_call(assistant_response)
        if parsed_response is None:
            return assistant_response

        history.append(call_tool(parsed_response))
        tool_calls += 1
        if tool_calls >= MAX_CONSECUTIVE_TOOL_CALLS:
            limit_message = (
                f"Error: Maximum of {MAX_CONSECUTIVE_TOOL_CALLS} consecutive tool calls reached. "
                "Please continue with a new request."
            )
            history.append({"role": "assistant", "content": limit_message})
            return limit_message

# NOTE: I tried multiple prompts to get one right
tools_prompt = """You are an assistant that can execute file tools. To use a tool, output exactly one JSON object with name and parameters, and nothing else. After emitting a tool call, end your response. The program will execute it and provide its result in an ipython message. Never invent file contents or tool results. If a task requires reading before writing, request the read first and wait for its result before requesting the write. When finished, answer in plain text.
You have access to the following tools: 'read_file', 'write_file' and 'search_file'.
You can ONLY USE ONE TOOL AT A TIME. If you need to use multiple tools, you must call them in separate responses.

1. 'read_file': Obtain the content of a file from disk.
   To use it, respond with a correct json: {"name": "read_file", "parameters": {"path": "FILE_PATH"}}

2. 'write_file': Write content to a file on disk. Only refer to files mentioned by the user or previously found by 'search_file'.
   To use it, respond with a correct json: {"name": "write_file", "parameters": {"path": "FILE_PATH", "content": "FILE_CONTENT"}}

3. 'search_file': search for a file on disk.
   To use it, respond with a correct json: {"name": "search_file", "parameters": {"path": "FILE_PATH", "file_name": "FILE_NAME"}}

When you need to use a tool, provide the required parameters in the JSON object and ANSWER ONLY with a single valid JSON string, example:
GOOD ANSWER: {"name": "search_file", "parameters": {"path": ".", "file_name": "my_file.txt"}}

IMPORTANT: DO NOT COMBINE MULTIPLE TOOL CALLS IN A SINGLE RESPONSE.
IMPORTANT: INVOKE A SINGLE FUNCTION THEN WAIT FOR THE RESULT BEFORE CALLING ANOTHER FUNCTION.

If you are not calling a tool, do not use JSON format."""

def chat(debug=False):
    # NOTE: we set the tool prompt a system to try give it an higher priority
    history= [{"role": "system", "content": tools_prompt}]
    # NOTE: also, we remove rules to avoid noise
    # history = load_rules()

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
            response = generate_response(history, debug=debug)

            print_system("Assistant: ", end="")
            print_assistant(response)
            
            if is_summarize:
                # Replace history with the summary while keeping rules
                history = load_rules()
                history.append({"role": "assistant", "content": f"Summary of previous chat history:\n{response}"})
            
        except Exception as e:
            print_error(f"Error: {e}")
            # Remove the last user message if it failed
            if history and history[-1]["role"] == "user":
                history.pop()

if __name__ == "__main__":
    debug = "--debug" in sys.argv
    chat(debug)
