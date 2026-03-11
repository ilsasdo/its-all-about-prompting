#!.venv/bin/python
import requests

def chat():
    url = "http://localhost:11434/api/generate"
    history = ""
    
    # ANSI color codes
    BLACK = "\033[30m"
    GREEN = "\033[32m"
    GRAY = "\033[90m"
    RESET = "\033[0m"
    
    print("Chat with LLM (type 'exit' or 'quit' to stop)")
    
    while True:
        user_input = input(f"{BLACK}You: ")
        print(RESET, end="")
        if user_input.lower() in ['exit', 'quit']:
            break
            
        # Append user input to history with USER: prefix
        history += f"USER: {user_input}\n"
        
        try:
            r = requests.post(
                url,
                json={
                    "model": "llama3.2",
                    "prompt": history + "SYSTEM: ",
                    "stream": False
                }
            )
            r.raise_for_status()
            response_data = r.json()
            assistant_response = response_data['response']
            
            prompt_tokens = response_data.get('prompt_eval_count', 0)
            eval_tokens = response_data.get('eval_count', 0)
            print(f"{GRAY}[Prompt: {prompt_tokens}, Response: {eval_tokens}, Total: {prompt_tokens + eval_tokens}]{RESET}")
            print(f"{GREEN}Assistant: {assistant_response}{RESET}")
            
            # Append assistant response to history with SYSTEM: prefix
            history += f"SYSTEM: {assistant_response}\n"
            
        except Exception as e:
            print(f"Error: {e}")
            # The last user message remains in history, but since it's a simple string, we could try to revert it or just leave it.
            # To be consistent with previous approach, let's remove it if it failed.
            history = history.rsplit(f"USER: {user_input}\n", 1)[0]

if __name__ == "__main__":
    chat()

# describe recursion with one sentence
# in italian
# in french
# with html formatting