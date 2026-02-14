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


def generate(prompt: str, model: str = "llama3.2") -> str:
    """Single completion from the local LLM."""
    toolsPrompt = """
You are a helpful assistant with access to a file-reading tool.

## Tool: read_file

- **Purpose**: Read the full text content of a file from the filesystem.
- **When to use**: When the user asks you to read, open, show, or inspect a file, or when you need file contents to answer their question.
- **When not to use**: Do not use it for general questions, explanations, or when no specific file is mentioned.

**Format** (use exactly this; it must be the only content on that line):
read_file("path/to/file")

- The path can be relative (e.g. "README.md") or absolute (e.g. "/etc/hosts").
- Use double quotes around the path. No other text on the same line.

**Examples**:
- read_file("README.md")
- read_file("/Users/me/project/config.json")

**Rules**:
1. If you need to read a file, output nothing else except the single line: read_file("path").
2. If you do not need to read a file, answer normally and do not output any read_file(...) line.
3. Never invent or guess file paths; use only paths the user gave or that are clearly implied.
"""
    
    response = ollama.generate(model=model, prompt=prompt, system=toolsPrompt)
    print(f"Prompt tokens: {response.get('prompt_eval_count', 0)}")
    print(f"Response tokens: {response.get('eval_count', 0)}")

    return response["response"]


# Tools declared in the system prompt (must match generate() toolsPrompt)
DECLARED_TOOLS = {"read_file", "read_webpage"}


def parse_tool_call(response: str) -> tuple[str, str] | None:
    """
    Parse the response for a tool call in the form tool_name(argument).
    Returns (tool_name, argument) if found, else None.
    """
    response = response.strip()
    # Match tool_name("arg") or tool_name('arg') or tool_name(arg)
    m = re.search(r"(\w+)\s*\(\s*[\"']?([^\"')]*)[\"']?\s*\)", response)
    if not m:
        return None
    name, arg = m.group(1), m.group(2).strip()
    if name in DECLARED_TOOLS and arg:
        return (name, arg)
    return None


def execute_tool(tool_name: str, argument: str) -> str:
    """
    Execute a declared tool (read_file or read_webpage) and return its result.
    """
    if tool_name == "read_file":
        try:
            with open(argument, encoding="utf-8") as f:
                file_content = f.read()
                return f"Here is the content of file {argument}:\n{file_content}\nEND OF FILE"
        except FileNotFoundError:
            return f"Error: file not found: {argument}"
        except OSError as e:
            return f"Error reading file: {e}"

    if tool_name == "read_webpage":
        try:
            with urlopen(argument, timeout=10) as resp:
                resp.read().decode("utf-8", errors="replace")
                return f"Here is the requested webpage content: {webpage_content}, continue your task."
        except URLError as e:
            return f"Error fetching URL: {e}"
        except Exception as e:
            return f"Error: {e}"

    return f"Unknown tool: {tool_name}"


if __name__ == "__main__":
    import sys

    model = sys.argv[1] if len(sys.argv) > 1 else "llama3.2"
    starting_prompt = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else None

    print(f"Model: {model}")
    print("Enter a prompt (or 'quit' / 'exit' to stop).\n")

    conversation_history = []

    while True:

        if starting_prompt is None:
            prompt = input("Prompt: ").strip()
        else:
            prompt = starting_prompt
            starting_prompt = None

        if prompt.lower() in ("quit", "exit"):
            print("Bye.")
            break

        conversation_history.append({"role": "user", "content": prompt})

        print(f"\033[90m{prompt}\033[0m")  # dark gray
        print("\nResponse:")
        response = generate(prompt, model=model)
        print(response)

        parsed = parse_tool_call(response)
        if parsed:
            tool_name, arg = parsed
            print(f"\nDetected tool call: {tool_name}({arg!r})")
            allow = input("Execute this command? [y/N]: ").strip().lower()
            if allow in ("y", "yes"):
                result = execute_tool(tool_name, arg)
                print("\nTool result:")
                print(result)
                conversation_history.append({"role": "tool", "content": result})
                starting_prompt = "\n\n".join(
                    f"{msg['role'].upper()}: {msg['content']}" for msg in conversation_history
                )
            else:
                print("Skipped.")

        print()

