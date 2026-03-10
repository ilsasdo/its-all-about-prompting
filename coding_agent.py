#!.venv/bin/python
"""
Coding Agent - An AI assistant specialized in code manipulation via Ollama.

Prerequisites:
  1. Install Ollama: https://ollama.com
  2. Pull a model: ollama pull llama3.2 (or codellama)
  3. pip install -r requirements.txt
"""

import re
import ast
import sys
import json
import subprocess
import ollama
from pathlib import Path


SYSTEM_PROMPT = """You are an expert coding assistant with access to specialized tools for code manipulation.

## Available Tools:

### read_file
- **Purpose**: Read the full content of a source code file.
- **When to use**: When you need to inspect, analyze, or understand existing code.
- **Arguments**: 
  - path (string): Path to the file to read

### write_file
- **Purpose**: Write or overwrite a file with new code content.
- **When to use**: When creating new code files or replacing file contents.
- **Arguments**:
  - path (string): Path to the file to write
  - content (string): Code content to write to the file

### analyze_code
- **Purpose**: Perform static analysis on a Python file to find syntax errors, style issues, and potential bugs.
- **When to use**: When you need to review code quality or find issues.
- **Arguments**:
  - path (string): Path to the Python file to analyze

### explain_code
- **Purpose**: Provide a detailed explanation of how code works.
- **When to use**: When the user asks to understand or explain code logic.
- **Arguments**:
  - path (string): Path to the file to explain

### run_code
- **Purpose**: Execute a Python script and capture its output.
- **When to use**: When you need to test code or see execution results.
- **Arguments**:
  - path (string): Path to the Python script to execute
  - args (string, optional): Command-line arguments to pass to the script

### refactor_code
- **Purpose**: Refactor existing code according to specific instructions.
- **When to use**: When improving code structure, readability, or performance.
- **Arguments**:
  - path (string): Path to the file to refactor
  - instructions (string): Refactoring instructions describing the desired changes

## Tool Call Format:

When you need to use a tool, respond with ONLY a JSON object in this exact format:

```json
{
  "tool": "tool_name",
  "args": {
    "arg_name": "arg_value"
  }
}
```

Examples:

Read a file:
```json
{
  "tool": "read_file",
  "args": {
    "path": "example.py"
  }
}
```

Write a file:
```json
{
  "tool": "write_file",
  "args": {
    "path": "hello.py",
    "content": "print('Hello, World!')"
  }
}
```

Run code:
```json
{
  "tool": "run_code",
  "args": {
    "path": "script.py",
    "args": "--verbose"
  }
}
```

## Rules:
1. If you need to use a tool, output ONLY the JSON object, nothing else (no markdown, no explanation).
2. If you don't need a tool, answer normally without any JSON.
3. Never invent file paths; use only paths the user provided or that clearly exist.
4. When writing code, ensure it's well-formatted, follows best practices, and includes necessary imports.
5. The JSON must be valid and properly escaped.
"""


def chat(messages: list[dict], model: str = "llama3.2") -> str:
    """Send messages to the LLM and return the response."""
    all_messages = [{"role": "system", "content": SYSTEM_PROMPT}] + messages
    
    response = ollama.chat(model=model, messages=all_messages, options={"temperature": 0.4})
    print(f"Prompt tokens: {response.get('prompt_eval_count', 0)}")
    print(f"Response tokens: {response.get('eval_count', 0)}")

    return response["message"]["content"]


# Tools declared in the system prompt
DECLARED_TOOLS = {"read_file", "write_file", "analyze_code", "explain_code", "run_code", "refactor_code"}


def format_messages(messages: list[dict]) -> str:
    """Format messages for display."""
    return "\n\n".join(
        f"{msg['role'].upper()}: {msg['content']}" for msg in messages
    )


def parse_tool_call(response: str) -> tuple[str, dict] | None:
    """
    Parse the response for a JSON tool call.
    Returns (tool_name, args_dict) if found, else None.
    
    Expected format:
    {
      "tool": "tool_name",
      "args": {"arg1": "value1", "arg2": "value2"}
    }
    """
    response = response.strip()
    
    # Try to extract JSON from markdown code blocks if present
    json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response, re.DOTALL)
    if json_match:
        json_str = json_match.group(1)
    else:
        # Try to find JSON object directly (look for complete {...} with "tool" key)
        # Match from first { to last }, accounting for nested objects
        brace_start = response.find('{')
        if brace_start != -1:
            brace_count = 0
            brace_end = -1
            for i in range(brace_start, len(response)):
                if response[i] == '{':
                    brace_count += 1
                elif response[i] == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        brace_end = i
                        break
            
            if brace_end != -1:
                json_str = response[brace_start:brace_end + 1]
            else:
                return None
        else:
            return None
    
    try:
        tool_call = json.loads(json_str)
        
        # Validate structure
        if not isinstance(tool_call, dict):
            return None
        if "tool" not in tool_call:
            return None
        
        tool_name = tool_call["tool"]
        if tool_name not in DECLARED_TOOLS:
            return None
        
        args = tool_call.get("args", {})
        if not isinstance(args, dict):
            return None
        
        return (tool_name, args)
    
    except json.JSONDecodeError:
        return None


def validate_python_syntax(code: str) -> tuple[bool, str]:
    """Validate Python code syntax. Returns (is_valid, error_message)."""
    try:
        ast.parse(code)
        return (True, "")
    except SyntaxError as e:
        return (False, f"Syntax error at line {e.lineno}: {e.msg}")


def execute_tool(tool_name: str, args: dict) -> str:
    """
    Execute a declared tool and return its result.
    Args is a dictionary of named arguments.
    """
    if tool_name == "read_file":
        path = args.get("path")
        if not path:
            return "Error: read_file requires 'path' argument"
        
        try:
            with open(path, encoding="utf-8") as f:
                file_content = f.read()
                return f"Here is the content of file {path}:\n{file_content}\nEND OF FILE"
        except FileNotFoundError:
            return f"Error: file not found: {path}"
        except OSError as e:
            return f"Error reading file: {e}"

    if tool_name == "write_file":
        path = args.get("path")
        content = args.get("content")
        
        if not path:
            return "Error: write_file requires 'path' argument"
        if content is None:
            return "Error: write_file requires 'content' argument"
        
        # Validate Python syntax if it's a .py file
        if path.endswith(".py"):
            is_valid, error_msg = validate_python_syntax(content)
            if not is_valid:
                return f"Error: Invalid Python syntax - {error_msg}"
        
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            return f"Successfully wrote to {path}"
        except OSError as e:
            return f"Error writing file: {e}"

    if tool_name == "analyze_code":
        path = args.get("path")
        if not path:
            return "Error: analyze_code requires 'path' argument"
        
        try:
            with open(path, encoding="utf-8") as f:
                code = f.read()
            
            # Basic static analysis
            issues = []
            
            # Check syntax
            is_valid, error_msg = validate_python_syntax(code)
            if not is_valid:
                issues.append(f"SYNTAX ERROR: {error_msg}")
            
            # Check for common issues
            lines = code.split("\n")
            for i, line in enumerate(lines, 1):
                # Check line length
                if len(line) > 120:
                    issues.append(f"Line {i}: Line too long ({len(line)} chars)")
                # Check for bare except
                if "except:" in line:
                    issues.append(f"Line {i}: Bare except clause (should specify exception type)")
                # Check for print statements (potential debug code)
                if line.strip().startswith("print("):
                    issues.append(f"Line {i}: Debug print statement found")
            
            if not issues:
                return f"Code analysis for {path}: No issues found. Code looks good!"
            else:
                return f"Code analysis for {path}:\n" + "\n".join(f"- {issue}" for issue in issues)
        
        except FileNotFoundError:
            return f"Error: file not found: {path}"
        except Exception as e:
            return f"Error analyzing code: {e}"

    if tool_name == "explain_code":
        path = args.get("path")
        if not path:
            return "Error: explain_code requires 'path' argument"
        
        try:
            with open(path, encoding="utf-8") as f:
                code = f.read()
            
            # Return code for LLM to explain
            return f"Here is the code from {path} that needs explanation:\n{code}\n\nPlease explain how this code works."
        except FileNotFoundError:
            return f"Error: file not found: {path}"
        except Exception as e:
            return f"Error reading file: {e}"

    if tool_name == "run_code":
        path = args.get("path")
        code_args = args.get("args", "")
        
        if not path:
            return "Error: run_code requires 'path' argument"
        
        try:
            # Build command
            cmd = [sys.executable, path]
            if code_args:
                cmd.extend(code_args.split())
            
            # Execute with timeout
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            output = f"Execution of {path}:\n"
            output += f"Exit code: {result.returncode}\n"
            if result.stdout:
                output += f"STDOUT:\n{result.stdout}\n"
            if result.stderr:
                output += f"STDERR:\n{result.stderr}\n"
            
            return output
        
        except subprocess.TimeoutExpired:
            return f"Error: Execution of {path} timed out (10 second limit)"
        except FileNotFoundError:
            return f"Error: file not found: {path}"
        except Exception as e:
            return f"Error executing code: {e}"

    if tool_name == "refactor_code":
        path = args.get("path")
        instructions = args.get("instructions")
        
        if not path:
            return "Error: refactor_code requires 'path' argument"
        if not instructions:
            return "Error: refactor_code requires 'instructions' argument"
        
        try:
            with open(path, encoding="utf-8") as f:
                code = f.read()
            
            # Return code and instructions for LLM to refactor
            return f"Here is the code from {path} that needs refactoring:\n{code}\n\nRefactoring instructions: {instructions}\n\nPlease provide the refactored code."
        except FileNotFoundError:
            return f"Error: file not found: {path}"
        except Exception as e:
            return f"Error reading file: {e}"

    return f"Unknown tool: {tool_name}"


if __name__ == "__main__":
    model = sys.argv[1] if len(sys.argv) > 1 else "llama3.2"
    initial_prompt = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else None

    print(f"Coding Agent (Model: {model})")
    print("Enter a coding task (or 'quit' / 'exit' to stop).\n")

    conversation_history = []

    while True:
        # Get user input (or use initial prompt if provided)
        if initial_prompt:
            user_input = initial_prompt
            initial_prompt = None
        else:
            user_input = input("Task: ").strip()

        if user_input.lower() in ("quit", "exit"):
            print("Bye.")
            break

        conversation_history.append({"role": "user", "content": user_input})

        # Keep calling LLM until no more tool calls
        while True:
            print(f"\033[90m{format_messages(conversation_history)}\033[0m")
            print("\nResponse:")
            response = chat(conversation_history, model=model)
            print(response)
            conversation_history.append({"role": "assistant", "content": response})

            parsed = parse_tool_call(response)
            if not parsed:
                break

            tool_name, args = parsed
            # Format args for display
            args_display = json.dumps(args, indent=2)
            print(f"\nDetected tool call: {tool_name}")
            print(f"Arguments:\n{args_display}")
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
