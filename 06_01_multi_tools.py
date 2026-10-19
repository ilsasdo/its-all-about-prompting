#!/usr/bin/env python3
import json
import sys
from pathlib import Path

from keyring.backends import null

from utils import llm_generate, print_user, print_system, print_error, print_assistant, print_debug

MAX_CONSECUTIVE_TOOL_CALLS = 10


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
        return [{"role": "system", "content": full_rules}]
    return []

def serialize_history(history: list[dict[str, str]]) -> str:
    prompt = "<|begin_of_text|>"
    for message in history:
        prompt += (
            f"<|start_header_id|>{message['role']}<|end_header_id|>\n\n"
            f"{message['content']}<|eot_id|>"
        )
    return prompt + "<|start_header_id|>assistant<|end_header_id|>\n\n"

def parse_tool_call(assistant_response: str, max_tool_calls: int = 10):
    try:
        clean_response = assistant_response.strip()
        if "```json" in clean_response:
            clean_response = clean_response.split("```json")[1].split("```")[
                0].strip()
        elif "```" in clean_response:
            clean_response = clean_response.split("```")[1].split("```")[
                0].strip()

        try:
            data = json.loads(clean_response)
        except json.JSONDecodeError:
            decoder = json.JSONDecoder()
            data = []
            offset = 0
            while offset < len(clean_response):
                while offset < len(clean_response) and clean_response[offset].isspace():
                    offset += 1
                if offset == len(clean_response):
                    break

                item, offset = decoder.raw_decode(clean_response, offset)
                data.append(item)

                while offset < len(clean_response) and clean_response[offset].isspace():
                    offset += 1
                if offset == len(clean_response):
                    break
                if clean_response[offset] != ";":
                    raise json.JSONDecodeError(
                        "Expected ';' between JSON objects",
                        clean_response,
                        offset,
                    )
                offset += 1

            if len(data) < 2:
                return {"role": "assistant", "content": assistant_response}

        if isinstance(data, dict):
            tool_calls = [data]
            return_list = False
        elif isinstance(data, list) and data and all(
                isinstance(item, dict) for item in data):
            tool_calls = data
            return_list = True
        else:
            return {"role": "assistant", "content": assistant_response}

        if not all(call.get("name") in ("read_file", "write_file", "search_file")
                   for call in tool_calls):
            return {"role": "assistant", "content": assistant_response}

        if max_tool_calls is not None:
            tool_calls = tool_calls[:max_tool_calls]

        results = []
        for call in tool_calls:
            tool_name = call["name"]
            parameters = call.get("parameters", {})
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
            results.append({"role": "tool", "content": result})

        return results if return_list else results[0]

    except (json.JSONDecodeError, IndexError):
        return {"role": "assistant", "content": assistant_response}


def read_file(path: str) -> str:
    """Read the content of a file from disk."""
    try:
        return f"The following is the content of file {path}:\n\n{Path(path).read_text()}"
    except Exception as e:
        return f"Error reading file {path}: {e}"


def write_file(path: str, content: str) -> str:
    """Write content to a file on disk."""
    try:
        Path(path).write_text(content)
        return f"File {path} written successfully."
    except Exception as e:
        return f"Error writing to file {path}: {e}"


def search_file(path: str, file_name: str) -> str:
    """Find files named file_name beneath the given directory."""
    try:
        search_path = Path(path)
        if not search_path.is_dir():
            return f"Error searching for {file_name}: {path} is not a directory."

        matches = sorted(
            candidate for candidate in search_path.rglob(file_name)
            if candidate.is_file()
        )
        if not matches:
            return f"No files named {file_name} found under {path}."

        return "Found files:\n" + "\n".join(str(match) for match in matches)
    except Exception as e:
        return f"Error searching for {file_name} under {path}: {e}"


def generate_response(history: list[dict[str, str]], debug: bool = False) -> str:
    """Generate a response, executing tool calls until the model responds normally."""
    tool_calls = 0
    while True:
        assistant_response = llm_generate(serialize_history(history), debug=debug)
        parsed_responses = parse_tool_call(
            assistant_response,
            max_tool_calls=MAX_CONSECUTIVE_TOOL_CALLS - tool_calls,
        )
        if not isinstance(parsed_responses, list):
            parsed_responses = [parsed_responses]

        if parsed_responses[0]["role"] != "tool":
            history.append(parsed_responses[0])
            return parsed_responses[0]["content"]

        history.extend(parsed_responses)
        tool_calls += len(parsed_responses)
        if tool_calls >= MAX_CONSECUTIVE_TOOL_CALLS:
            limit_message = (
                f"Error: Maximum of {MAX_CONSECUTIVE_TOOL_CALLS} consecutive tool calls reached. "
                "Please continue with a new request."
            )
            history.append({"role": "assistant", "content": limit_message})
            return limit_message


tools_prompt = """You have access to the following tools: 'read_file', 'write_file' and 'search_file'.

1. 'read_file': Obtain the content of a file from disk.
   To use it, respond with a correct json: {"name": "read_file", "parameters": {"path": "FILE_PATH"}}

2. 'write_file': Write content to a file on disk. Only refer to files mentioned by the user or previously found by 'search_file'.
   To use it, respond with a correct json: {"name": "write_file", "parameters": {"path": "FILE_PATH", "content": "FILE_CONTENT"}}

3. 'search_file': search for a file on disk.
   To use it, respond with a correct json: {"name": "search_file", "parameters": {"path": "FILE_PATH", "file_name": "FILE_NAME"}}

When you need to use a tool, provide the required parameters in the JSON object and ANSWER ONLY with a single valid JSON ARRAY string, example:
GOOD ANSWER: [{"name": "search_file", "parameters": {"path": ".", "file_name": "my_file.txt"}}]
BAD ANSWER: {"name": "search_file", "parameters": {"path": ".", "file_name": "my_file.txt"}}; {"name": "search_file", "parameters": {"path": ".", "file_name": "another_file.txt"}}

If you are not calling a tool, do not use JSON format."""

def chat(debug=False):
    history = load_rules()
    history.append({"role": "system", "content": tools_prompt})
    
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
