#!.venv/bin/python
import requests
import sys
import json

GRAY = "\033[90m"
RESET = "\033[0m"

def call_llm(prompt, debug=False):
    url = "http://localhost:11434/api/generate"
    payload = {
        "model": "llama3.2",
        "prompt": prompt,
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

def generate(prompt, debug=False):
    response_data = call_llm(prompt, debug)
    prompt_tokens = response_data.get('prompt_eval_count', 0)
    eval_tokens = response_data.get('eval_count', 0)
    print(f"{GRAY}[Prompt: {prompt_tokens}, Response: {eval_tokens}, Total: {prompt_tokens + eval_tokens}]{RESET}")
    return response_data['response']

if __name__ == "__main__":
    debug = "--debug" in sys.argv
    print(generate("Explain recursion in one sentence.", debug))
