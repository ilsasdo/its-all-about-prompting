#!.venv/bin/python
import requests
from pathlib import Path
import sys
import json

GRAY = "\033[90m"
RESET = "\033[0m"

def call_llm(messages, tools=None, debug=False):
    url = "http://localhost:11434/api/chat"
    payload = {
        "model": "llama3.2",
        "messages": messages,
        # "temperature": 0.4,
        "stream": False
    }
    
    if tools:
        payload["tools"] = tools
    
    if debug:
        print(f"{GRAY}Request: {json.dumps(payload, indent=2)}{RESET}")
        
    r = requests.post(url, json=payload)
    r.raise_for_status()
    response_data = r.json()
    
    if debug:
        print(f"{GRAY}Response: {json.dumps(response_data, indent=2)}{RESET}")
        
    return response_data

def load_rules(rules_dir_path: str = "./rules") -> list:
    rules = []
    rules_dir = Path(rules_dir_path)
    if rules_dir.exists():
        for rule_file in sorted(rules_dir.glob("*.txt")):
            rule_content = rule_file.read_text().strip()
            if rule_content:
                rules.append({"role": "system", "content": rule_content})
    return rules

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

def chat(debug=False):
    history = load_rules()
    
    # ANSI color codes
    BLACK = "\033[30m"
    GREEN = "\033[32m"
    
    print("Chat with LLM (type 'exit' or 'quit' to stop, '/plan' to generate a plan, '/summarize' to summarize chat, '/tools' to show tool definitions)")
    
    PLAN_PROMPT = """Analyze the task and provide a detailed step-by-step plan for its execution.
Identify potential risks, dependencies, and key milestones.
Format the output as a numbered list with clear explanations for each step."""

    SUMMARIZE_PROMPT = """Summarize the current chat history into a concise yet detailed summary.
    Retain the most relevant information and current task context.
    The summary will be used to reduce the context size, so it must capture the essence of the entire conversation."""

    TOOLS = [
        {
            "type": "function",
            "function": {
                "name": "read_file",
                "description": "Read the content of a file from disk.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "The path to the file to read."
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
                "description": "Write content to a file on disk.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "The path to the file to write to."
                        },
                        "content": {
                            "type": "string",
                            "description": "The content to write to the file."
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
            response_data = call_llm(history, tools=TOOLS, debug=debug)
            message = response_data['message']
            assistant_response = message.get('content', '')
            
            prompt_tokens = response_data.get('prompt_eval_count', 0)
            eval_tokens = response_data.get('eval_count', 0)
            print(f"{GRAY}[Prompt: {prompt_tokens}, Response: {eval_tokens}, Total: {prompt_tokens + eval_tokens}]{RESET}")
            
            if assistant_response:
                print(f"{GREEN}Assistant: {assistant_response}{RESET}")
            
            # Detect tool call
            if 'tool_calls' in message:
                for tool_call in message['tool_calls']:
                    tool_name = tool_call['function']['name']
                    parameters = tool_call['function']['arguments']
                    
                    print(f"{GRAY}Tool call: {tool_name}({parameters}){RESET}")
                    
                    if tool_name == "read_file":
                        result = read_file(parameters.get("path"))
                    elif tool_name == "write_file":
                        result = write_file(parameters.get("path"), parameters.get("content"))
                    else:
                        result = f"Error: Tool {tool_name} not found."
                    
                    print(f"{GRAY}Tool result: {result}{RESET}")
                    
                    # Append assistant tool call and tool result to history
                    # For Ollama, the tool result role is "tool" and it needs the tool name or call ID
                    history.append(message)
                    history.append({"role": "tool", "tool_name": tool_name, "content": result})
                    
                # Call LLM again with tool result
                response_data = call_llm(history, tools=TOOLS, debug=debug)
                assistant_response = response_data['message']['content']
                print(f"{GREEN}Assistant: {assistant_response}{RESET}")

            if is_summarize:
                # Replace history with the summary while keeping rules
                history = load_rules()
                history.append({"role": "assistant", "content": f"Summary of previous chat history:\n{assistant_response}"})
            else:
                # Append assistant response to history
                history.append({"role": "assistant", "content": assistant_response})
            
        except Exception as e:
            print(f"Error: {e}")
            # Remove the last user message if it failed
            if history and history[-1]["role"] == "user":
                history.pop()

if __name__ == "__main__":
    debug = "--debug" in sys.argv
    chat(debug)