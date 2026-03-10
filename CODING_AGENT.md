# Coding Agent

A specialized AI coding assistant powered by Ollama that can read, write, analyze, execute, and refactor code through an interactive command-line interface with JSON-based tool calling.

## Features

- **Code Generation**: Create new code from natural language descriptions
- **Code Analysis**: Perform static analysis to find syntax errors and code issues
- **Code Execution**: Run Python scripts and capture output
- **Code Explanation**: Get detailed explanations of how code works
- **Code Refactoring**: Improve code structure and readability
- **Interactive Mode**: Conversational interface with tool execution confirmation
- **JSON Tool Calls**: Structured, reliable tool invocation format

## Prerequisites

1. **Install Ollama**: https://ollama.com
   ```bash
   brew install ollama
   ```

2. **Pull a model**:
   ```bash
   ollama pull llama3.2
   # Or for better coding performance:
   ollama pull codellama
   ```

3. **Set up Python environment**:
   ```bash
   python3 -m venv .venv
   .venv/bin/pip install -r requirements.txt
   ```

## Usage

### Interactive Mode

```bash
.venv/bin/python coding_agent.py [model]
```

Examples:
```bash
# Use default model (llama3.2)
.venv/bin/python coding_agent.py

# Use codellama for better coding results
.venv/bin/python coding_agent.py codellama

# Or make it executable
chmod +x coding_agent.py
./coding_agent.py codellama
```

### One-shot Command

```bash
.venv/bin/python coding_agent.py llama3.2 "your coding task here"
```

Example:
```bash
.venv/bin/python coding_agent.py codellama "create a function to calculate prime numbers"
```

## JSON Tool Call Format

The agent uses structured JSON for tool calls, making parsing reliable and explicit. When the LLM needs to use a tool, it responds with:

```json
{
  "tool": "tool_name",
  "args": {
    "arg_name": "arg_value"
  }
}
```

### Example Tool Calls

**Read a file:**
```json
{
  "tool": "read_file",
  "args": {
    "path": "example.py"
  }
}
```

**Write a file:**
```json
{
  "tool": "write_file",
  "args": {
    "path": "hello.py",
    "content": "print('Hello, World!')"
  }
}
```

**Analyze code:**
```json
{
  "tool": "analyze_code",
  "args": {
    "path": "script.py"
  }
}
```

**Run code with arguments:**
```json
{
  "tool": "run_code",
  "args": {
    "path": "script.py",
    "args": "--verbose"
  }
}
```

## Available Tools

### read_file
Read the content of a source code file.
- **Arguments**: `path` (string) - Path to the file to read

### write_file
Write or overwrite a file with code (includes Python syntax validation).
- **Arguments**: 
  - `path` (string) - Path to the file to write
  - `content` (string) - Code content to write

### analyze_code
Perform static analysis to find syntax errors, style issues, and potential bugs.
- **Arguments**: `path` (string) - Path to the Python file to analyze

### explain_code
Get a detailed explanation of how code works.
- **Arguments**: `path` (string) - Path to the file to explain

### run_code
Execute a Python script and capture its output (10 second timeout).
- **Arguments**:
  - `path` (string) - Path to the Python script
  - `args` (string, optional) - Command-line arguments

### refactor_code
Refactor existing code according to specific instructions.
- **Arguments**:
  - `path` (string) - Path to the file to refactor
  - `instructions` (string) - Refactoring instructions

## Safety Features

- **User confirmation required** for all tool executions
- **Syntax validation** before writing Python files
- **Execution timeout** (10 seconds) to prevent runaway processes
- **Structured JSON parsing** for reliable tool call detection
- **Clear argument display** showing exactly what will be executed

## Example Sessions

### Code Generation
```
Task: create a fibonacci function in fib.py

Response: 
{
  "tool": "write_file",
  "args": {
    "path": "fib.py",
    "content": "def fibonacci(n):\n    ..."
  }
}

Execute this command? [y/N]: y
Successfully wrote to fib.py
```

### Code Analysis
```
Task: check the code quality of my_script.py

Response:
{
  "tool": "analyze_code",
  "args": {
    "path": "my_script.py"
  }
}

Execute this command? [y/N]: y
Code analysis: Line 45: Line too long (135 chars)
```

## Tips

- Use **codellama** model for better coding-specific results
- Be specific in your requests for better tool usage
- Review tool calls before confirming execution
- The agent maintains conversation history across multiple turns
- Type `quit` or `exit` to end the session
- JSON format ensures reliable tool parsing and clear intent

## Architecture

Built on the same foundation as agent007.py but specialized for coding:
- Ollama API integration for LLM inference
- **JSON-based tool calling** for structured, reliable parsing
- Conversational history management
- Safety confirmations for file operations
- Named arguments for better clarity and maintainability
