#!.venv/bin/python
import requests
import json
import argparse
import sys
from pathlib import Path

# ANSI color codes
BLACK = "\033[30m"
RED = "\033[31m"
GREEN = "\033[32m"
GRAY = "\033[90m"
RESET = "\033[0m"

DEBUG = False

def read_file(path: str) -> str:
    try:
        return Path(path).read_text()
    except Exception as e:
        return f"Error reading file {path}: {e}"

def write_file(path: str, content: str) -> str:
    try:
        Path(path).write_text(content)
        return f"File {path} written successfully."
    except Exception as e:
        return f"Error writing to file {path}: {e}"

def load_rules(rules_dir_path: str = "./rules") -> list:
    rules = []
    rules_dir = Path(rules_dir_path)
    if rules_dir.exists():
        for rule_file in sorted(rules_dir.glob("*.txt")):
            rule_content = rule_file.read_text().strip()
            if rule_content:
                rules.append({"role": "system", "content": rule_content})
    return rules

def llm_request(url: str, model: str, messages: list, tools: list = None) -> dict:
    payload = {
        "model": model,
        "messages": messages,
        "stream": False,
        "options": {
            "temperature": 0.1
        }
    }
    if tools:
        payload["tools"] = tools
        
    if DEBUG:
        print(f"{GRAY}--- Request ---{RESET}")
        print(f"{GRAY}{json.dumps(payload, indent=2)}{RESET}")

    r = requests.post(url, json=payload)
    try:
        r.raise_for_status()
    except requests.exceptions.HTTPError as e:
        print(f"{RED}Error response from LLM: {r.text}{RESET}")
        raise e
    response_json = r.json()
    
    if DEBUG:
        print(f"{GRAY}--- Response ---{RESET}")
        print(f"{GRAY}{json.dumps(response_json, indent=2)}{RESET}")
        
    return response_json

def chat():
    url = "http://localhost:11434/api/chat"
    history = load_rules()
    
    print("Chat with LLM (type 'exit' or 'quit' to stop, '/plan' to generate a plan, '/summarize' to summarize chat)")
    
    PLAN_PROMPT = """Analyze the task and provide a detailed step-by-step plan for its execution.
Identify potential risks, dependencies, and key milestones.
Format the output as a numbered list with clear explanations for each step."""

    SUMMARIZE_PROMPT = """Summarize the current chat history into a concise yet detailed summary.
Retain the most relevant information and current task context.
The summary will be used to reduce the context size, so it must capture the essence of the entire conversation."""

    tools = [
        {
            "type": "function",
            "function": {
                "name": "read_file",
                "description": "Read the content of a file from disk",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "The path to the file to read"
                        }
                    },
                    "required": ["path"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "write_file",
                "description": "Write content to a file on disk",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "The path to the file to write"
                        },
                        "content": {
                            "type": "string",
                            "description": "The content to write to the file"
                        }
                    },
                    "required": ["path", "content"]
                }
            }
        }
    ]

    while True:
        user_input = input(f"{BLACK}You: ")
        print(RESET, end="")
        if user_input.lower() in ['exit', 'quit']:
            break
            
        is_summarize = False
        if user_input.strip().lower() == '/plan':
            history.append({"role": "user", "content": PLAN_PROMPT})
        elif user_input.strip().lower() == '/summarize':
            history.append({"role": "user", "content": SUMMARIZE_PROMPT})
            is_summarize = True
        else:
            # Append user input to history
            history.append({"role": "user", "content": user_input})
        
        try:
            response_data = llm_request(url, "llama3.2", history, tools)
            print(response_data)
            message = response_data['message']
            assistant_response = message.get('content', '')
            tool_calls = message.get('tool_calls', [])
            
            prompt_tokens = response_data.get('prompt_eval_count', 0)
            eval_tokens = response_data.get('eval_count', 0)
            print(f"{GRAY}[Prompt: {prompt_tokens}, Response: {eval_tokens}, Total: {prompt_tokens + eval_tokens}]{RESET}")
            
            if assistant_response:
                print(f"{GREEN}Assistant: {assistant_response}{RESET}")
            
            # Append assistant response to history
            history.append(message)

            if tool_calls:
                for tool_call in tool_calls:
                    function_name = tool_call['function']['name']
                    arguments = tool_call['function']['arguments']
                    print(f"{GRAY}[Tool Call: {function_name}({arguments})]{RESET}")
                    
                    if function_name == "read_file":
                        result = f"Here is the content of requested file {arguments.get('path')}:\n {read_file(arguments.get('path'))}"
                    elif function_name == "write_file":
                        result = write_file(arguments.get('path'), arguments.get('content'))
                    else:
                        result = f"Error: Tool {function_name} not found."
                    
                    history.append({
                        "role": "tool",
                        "content": result
                    })
                
                # Get final response from assistant after tool execution
                print(f"{GRAY}{history}")
                response_data = llm_request(url, "llama3.2", history)
                assistant_response = response_data['message']['content']
                print(f"{GREEN}Assistant: {assistant_response}{RESET}")
                history.append(response_data['message'])

            if is_summarize:
                # Replace history with the summary while keeping rules
                history = load_rules()
                history.append({"role": "assistant", "content": f"Summary of previous chat history:\n{assistant_response}"})
            
        except Exception as e:
            print(f"{RED}Error: {e}{RESET}")
            # Remove the last user message if it failed
            if history and history[-1]["role"] == "user":
                history.pop()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Chat with LLM with tool calling support")
    parser.add_argument("--debug", action="store_true", help="Enable debug messages")
    args = parser.parse_args()
    
    DEBUG = args.debug
    chat()

# chats:
# I want to build a simple chess engine in python. what should I do?