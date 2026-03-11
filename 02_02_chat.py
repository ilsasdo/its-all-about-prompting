#!.venv/bin/python
import requests
import sys
import json

GRAY = "\033[90m"
RESET = "\033[0m"

def call_llm(messages, debug=False):
    url = "http://localhost:11434/api/chat"
    payload = {
        "model": "llama3.2",
        "messages": messages,
        "stream": False
    }
    
    if debug:
        print(f"{GRAY}Request: {json.dumps(payload, indent=2)}{RESET}")
        
    r = requests.post(url, json=payload)
    r.raise_for_status()
    response_data = r.json()
    
    if debug:
        print(f"{GRAY}Response: {json.dumps(response_data, indent=2)}{RESET}")
        
    return response_data

def chat(debug=False):
    history = []
    
    # ANSI color codes
    BLACK = "\033[30m"
    GREEN = "\033[32m"
    
    print("Chat with LLM (type 'exit' or 'quit' to stop)")
    
    while True:
        user_input = input(f"{BLACK}You: ")
        print(RESET, end="")
        if user_input.lower() in ['exit', 'quit']:
            break
            
        # Append user input to history
        history.append({"role": "user", "content": user_input})
        
        try:
            response_data = call_llm(history, debug)
            assistant_response = response_data['message']['content']
            
            prompt_tokens = response_data.get('prompt_eval_count', 0)
            eval_tokens = response_data.get('eval_count', 0)
            print(f"{GRAY}[Prompt: {prompt_tokens}, Response: {eval_tokens}, Total: {prompt_tokens + eval_tokens}]{RESET}")
            print(f"{GREEN}Assistant: {assistant_response}{RESET}")
            
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
