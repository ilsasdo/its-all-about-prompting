import requests
import json

GRAY = "\033[90m"
RESET = "\033[0m"
BLACK = "\033[30m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
RED = "\033[31m"

def print_yellow(text, end="\n"):
    print(f"{YELLOW}{text}{RESET}", end=end)

def print_green(text, end="\n"):
    print(f"{GREEN}{text}{RESET}", end=end)

def print_black(text, end="\n"):
    print(f"{BLACK}{text}{RESET}", end=end)

def print_gray(text, end="\n"):
    print(f"{GRAY}{text}{RESET}", end=end)

def print_red(text, end="\n"):
    print(f"{RED}{text}{RESET}", end=end)

def print_system(text, end="\n"):
    print_green(text, end=end)

def print_error(text, end="\n"):
    print_red(text, end=end)

def print_user(text, end="\n"):
    print_black(text, end=end)

def print_debug(text, end="\n"):
    print_gray(text, end=end)

def print_assistant(text, end="\n"):
    print_yellow(text, end=end)

def llm_post_request(url, payload, debug=False, verbose=False):
    if debug:
        print_debug(f"Request: {json.dumps(payload, indent=2)}")
        
    r = requests.post(url, json=payload)
    r.raise_for_status()
    response_data = r.json()
    
    if debug:
        if verbose:
            response_debug = json.dumps(response_data, indent=2)
        else:
            response_value = response_data.get('response')
            if response_value is None:
                message = response_data.get('message')
                if isinstance(message, dict):
                    response_value = message.get('content')
            response_debug = str(response_value)
        print_debug(f"Response: {response_debug}")
        
    _print_token_usage(response_data)
    return response_data

def llm_generate(prompt, debug=False, verbose=False):
    url = "http://localhost:11434/api/generate"
    payload = {
        "model": "llama3.2",
        "prompt": prompt,
        "stream": False
    }
    response_data = llm_post_request(url, payload, debug, verbose)
    return response_data['response']

def llm_chat(messages, tools=None, debug=False, verbose=False):
    url = "http://localhost:11434/api/chat"
    payload = {
        "model": "llama3.2",
        "messages": messages,
        "stream": False
    }
    if tools:
        payload["tools"] = tools
    return llm_post_request(url, payload, debug, verbose)


def _print_token_usage(response_data):
    prompt_tokens = response_data.get('prompt_eval_count', 0)
    eval_tokens = response_data.get('eval_count', 0)
    print_debug(f"[Prompt: {prompt_tokens}, Response: {eval_tokens}, Total: {prompt_tokens + eval_tokens}]")
