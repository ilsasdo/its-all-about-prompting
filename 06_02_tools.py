#!/usr/bin/env python3
from pathlib import Path
import sys
import json
from utils import llm_chat, print_user, print_system, print_error, print_assistant, print_debug

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
        try:
            print_user("You: ", end="")
            user_input = input()
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
            
            response_data = llm_chat(history, tools=TOOLS, debug=debug)
            message = response_data['message']
            assistant_response = message.get('content', '')
            
            if assistant_response:
                print_system("Assistant: ", end="")
                print_assistant(assistant_response)
            
            # Detect tool call
            if 'tool_calls' in message:
                for tool_call in message['tool_calls']:
                    tool_name = tool_call['function']['name']
                    parameters = tool_call['function']['arguments']
                    
                    print_debug(f"Tool call: {tool_name}({parameters})")
                    
                    if tool_name == "read_file":
                        result = read_file(parameters.get("path"))
                    elif tool_name == "write_file":
                        result = write_file(parameters.get("path"), parameters.get("content"))
                    else:
                        result = f"Error: Tool {tool_name} not found."
                    
                    print_debug(f"Tool result: {result}")
                    
                    # Append assistant tool call and tool result to history
                    # For Ollama, the tool result role is "tool" and it needs the tool name or call ID
                    history.append(message)
                    history.append({"role": "tool", "tool_name": tool_name, "content": result})
                    history.append({"role": "user", "content": f"Tell me what you just did."})
                    
                # Call LLM again with tool result
                response_data = llm_chat(history, tools=TOOLS, debug=debug)
                assistant_response = response_data['message']['content']
                print_system("Assistant: ", end="")
                print_assistant(assistant_response)

            if is_summarize:
                # Replace history with the summary while keeping rules
                history = load_rules()
                history.append({"role": "assistant", "content": f"Summary of previous chat history:\n{assistant_response}"})
            else:
                # Append assistant response to history
                history.append({"role": "assistant", "content": assistant_response})
            
        except Exception as e:
            print_error(f"Error: {e}")
            # Remove the last user message if it failed
            if history and history[-1]["role"] == "user":
                history.pop()

if __name__ == "__main__":
    debug = "--debug" in sys.argv
    chat(debug)