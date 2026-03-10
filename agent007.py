#!.venv/bin/python
"""
Invoke a local LLM via Ollama.

Prerequisites:
  1. Install Ollama: https://ollama.com
  2. Pull a model: ollama pull llama3.2  (or llama2, mistral, etc.)
  3. pip install -r requirements.txt
"""

import re
import ollama
from urllib.request import urlopen
from urllib.error import URLError


SYSTEM_PROMPT = """You are a helpful assistant with access to tools.

## Tool: read_file

- **Purpose**: Read the full text content of a file from the filesystem.
- **When to use**: When the user asks you to read, open, show, or inspect a file.

**Format**: read_file("path/to/file")

## Tool: write_file

- **Purpose**: Write content to a file on the filesystem.
- **When to use**: When the user asks you to create, write, or save content to a file.

**Format**: write_file("path/to/file", \"\"\"content to write\"\"\")

**Rules**:
1. If you need to use a tool, output nothing else except the single tool call line.
2. If you do not need a tool, answer normally without any tool call.
3. Never invent or guess file paths; use only paths the user gave or that are clearly implied.
"""


def chat(messages: list[dict], model: str = "llama3.2") -> str:
    """Send messages to the LLM and return the response."""
    all_messages = [{"role": "system", "content": SYSTEM_PROMPT}] + messages
    
    response = ollama.chat(model=model, messages=all_messages, options={"temperature": 0.4})
    print(f"Prompt tokens: {response.get('prompt_eval_count', 0)}")
    print(f"Response tokens: {response.get('eval_count', 0)}")

    return response["message"]["content"]


# Tools declared in the system prompt (must match generate() toolsPrompt)
DECLARED_TOOLS = {"read_file", "read_webpage", "write_file"}


def format_messages(messages: list[dict]) -> str:
    """Format messages for display."""
    return "\n\n".join(
        f"{msg['role'].upper()}: {msg['content']}" for msg in messages
    )


def parse_tool_call(response: str) -> tuple[str, list[str]] | None:
    """
    Parse the response for a tool call in the form tool_name(arg1, arg2, ...).
    Returns (tool_name, [args]) if found, else None.
    """
    response = response.strip()
    # Match tool_name(...) 
    m = re.search(r"(\w+)\s*\((.*)\)", response, re.DOTALL)
    if not m:
        return None
    name = m.group(1)
    if name not in DECLARED_TOOLS:
        return None
    # Extract quoted arguments
    args_str = m.group(2)
    args = re.findall(r'["\']([^"\']*)["\']', args_str)
    if args:
        return (name, args)
    return None


def execute_tool(tool_name: str, args: list[str]) -> str:
    """
    Execute a declared tool and return its result.
    """
    if tool_name == "read_file":
        path = args[0]
        try:
            with open(path, encoding="utf-8") as f:
                file_content = f.read()
                return f"Here is the content of file {path}:\n{file_content}\nEND OF FILE"
        except FileNotFoundError:
            return f"Error: file not found: {path}"
        except OSError as e:
            return f"Error reading file: {e}"

    if tool_name == "write_file":
        if len(args) < 2:
            return "Error: write_file requires path and content arguments"
        path, content = args[0], args[1]
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            return f"Successfully wrote to {path}"
        except OSError as e:
            return f"Error writing file: {e}"

    if tool_name == "read_webpage":
        url = args[0]
        try:
            with urlopen(url, timeout=10) as resp:
                webpage_content = resp.read().decode("utf-8", errors="replace")
                return f"Here is the requested webpage content: {webpage_content}, continue your task."
        except URLError as e:
            return f"Error fetching URL: {e}"
        except Exception as e:
            return f"Error: {e}"

    return f"Unknown tool: {tool_name}"


if __name__ == "__main__":
    import sys

    model = sys.argv[1] if len(sys.argv) > 1 else "llama3.2"
    initial_prompt = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else None

    print(f"Model: {model}")
    print("Enter a prompt (or 'quit' / 'exit' to stop).\n")

    conversation_history = []

    while True:
        # Get user input (or use initial prompt if provided)
        if initial_prompt:
            user_input = initial_prompt
            initial_prompt = None
        else:
            user_input = input("Prompt: ").strip()

        if user_input.lower() in ("quit", "exit"):
            print("Bye.")
            break

        conversation_history.append({"role": "user", "content": user_input})

        # Keep calling LLM until no more tool calls
        while True:
            print(f"\033[90m{format_messages(conversation_history)}\033[0m")  # dark gray
            print("\nResponse:")
            response = chat(conversation_history, model=model)
            print(response)
            conversation_history.append({"role": "assistant", "content": response})

            parsed = parse_tool_call(response)
            if not parsed:
                break

            tool_name, args = parsed
            args_display = ", ".join(repr(a) for a in args)
            print(f"\nDetected tool call: {tool_name}({args_display})")
            allow = input("Execute this command? [y/N]: ").strip().lower()
            if allow in ("y", "yes"):
                result = execute_tool(tool_name, args)
                print("\nTool result:")
                print(result)
                conversation_history.append({"role": "user", "content": f"[TOOL RESULT]\n{result}"})
            else:
                print("Skipped.")
                break

        print()

