#!.venv/bin/python
"""
Invoke a local LLM via Ollama.

Prerequisites:
  1. Install Ollama: https://ollama.com
  2. Pull a model: ollama pull llama3.2  (or llama2, mistral, etc.)
  3. pip install -r requirements.txt
"""

import ollama


def generate(prompt: str, model: str = "llama3.2") -> str:
    """Single completion from the local LLM."""
    toolsPrompt = """
    You have the following tools at your disposal:
    - read_file(file_path) to read the content of a file.
    - read_webpage(url) to read the content of a webpage.

    Whenever you need to use a tool, you must call the tool using the following format as the only response without any other text or syntax:
    tool_name(arguments)
    """
    response = ollama.generate(model=model, prompt=prompt, system=toolsPrompt)
    return response["response"]


def chat(messages: list[dict], model: str = "llama3.2") -> str:
    """Chat with the local LLM (multi-turn)."""
    response = ollama.chat(model=model, messages=messages)
    return response["message"]["content"]


def stream(prompt: str, model: str = "llama3.2"):
    """Stream the response token by token."""
    stream = ollama.generate(model=model, prompt=prompt, stream=True)

    for chunk in stream:
        if chunk.get("response"):
            print(chunk["response"], end="", flush=True)
    print()


if __name__ == "__main__":
    import sys

    model = sys.argv[1] if len(sys.argv) > 1 else "llama3.2"
    prompt = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else "Explain what a local LLM is in one sentence."

    print(f"Model: {model}\nPrompt: {prompt}\n")
    print("Response:")
    print(generate(prompt, model=model))

    
