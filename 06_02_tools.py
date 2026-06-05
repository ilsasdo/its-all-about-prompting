#!/usr/bin/env python3
import json
import sys
from pathlib import Path

from utils import llm_chat, print_user, print_system, print_error, \
  print_assistant, print_debug


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

  print(
    "Chat with LLM (type 'exit' or 'quit' to stop, '/plan' to generate a plan, '/summarize' to summarize chat, '/tools' to show tool definitions)")

  PLAN_PROMPT = """Analyze the task and provide a detailed step-by-step plan for its execution.
Identify potential risks, dependencies, and key milestones.
Format the output as a numbered list with clear explanations for each step."""

  SUMMARIZE_PROMPT = """Summarize the current chat history into a concise yet detailed summary.
    Retain the most relevant information and current task context.
    The summary will be used to reduce the context size, so it must capture the essence of the entire conversation."""

  TOOLS_PROMPT = """You have access to two tools: 'read_file' and 'write_file'.

1. 'read_file': Obtain the content of a file from disk.
   To use it, respond with a correct json: {"name": "read_file", "parameters": {"path": "FILE_PATH"}}

2. 'write_file': Write content to a file on disk.
   To use it, respond with a correct json: {"name": "write_file", "parameters": {"path": "FILE_PATH", "content": "FILE_CONTENT"}}

When you need to use a tool, provide the required parameters in the JSON object and ANSWER ONLY with a single valid JSON string.
If you are not calling a tool, do not use JSON format."""

  history.append({"role": "system", "content": TOOLS_PROMPT})

  while True:
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

    try:
      response_data = llm_chat(history, debug=debug)
      assistant_response = response_data['message']['content']

      print_system("Assistant: ", end="")
      print_assistant(assistant_response)

      # Detect tool call
      try:
        # Basic cleaning of the response to find JSON
        clean_response = assistant_response.strip()
        if "```json" in clean_response:
          clean_response = clean_response.split("```json")[1].split("```")[
            0].strip()
        elif "```" in clean_response:
          clean_response = clean_response.split("```")[1].split("```")[
            0].strip()

        data = json.loads(clean_response)
        if isinstance(data, dict) and (
            data.get("name") == "read_file" or data.get(
          "name") == "write_file"):
          tool_name = data["name"]
          parameters = data.get("parameters", {})

          print_debug(f"Tool call: {tool_name}({parameters})")

          if tool_name == "read_file":
            result = read_file(parameters.get("path"))
          elif tool_name == "write_file":
            result = write_file(parameters.get("path"),
                                parameters.get("content"))
          else:
            result = f"Error: Tool {tool_name} not found."

          print_debug(f"Tool result: {result}")

          # Append assistant tool call and system result to history
          history.append({"role": "tool", "tool_name": tool_name, "content": result})
          history.append({"role": "user", "content": f"Tell me what you just did."})

          response_data = llm_chat(history, debug=debug)
          assistant_response = response_data['message']['content']
          print_system("Assistant: ", end="")
          print_assistant(assistant_response)
      except (json.JSONDecodeError, IndexError):
        pass

      if is_summarize:
        # Replace history with the summary while keeping rules
        history = load_rules()
        history.append({"role": "assistant",
                        "content": f"Summary of previous chat history:\n{assistant_response}"})
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

# chats:
# I want to build a simple chess engine in python. what should I do?
