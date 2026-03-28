#!.venv/bin/python
import sys
from utils import call_llm, print_token_usage, RESET, GRAY

def chat(debug=False):
    history = ""
    
    # ANSI color codes
    BLACK = "\033[30m"
    GREEN = "\033[32m"
    
    print("Chat with LLM (type 'exit' or 'quit' to stop)")
    
    while True:
        user_input = input(f"{BLACK}You: ")
        print(RESET, end="")
        if user_input.lower() in ['exit', 'quit']:
            break
            
        # Append user input to history with USER: prefix
        history += f"USER: {user_input}\n"
        
        try:
            response_data = call_llm(history + "SYSTEM: ", debug)
            assistant_response = response_data['response']
            
            print_token_usage(response_data)
            print(f"{GREEN}Assistant: {assistant_response}{RESET}")
            
            # Append assistant response to history with SYSTEM: prefix
            history += f"SYSTEM: {assistant_response}\n"
            
        except Exception as e:
            print(f"Error: {e}")
            # The last user message remains in history, but since it's a simple string, we could try to revert it or just leave it.
            # To be consistent with previous approach, let's remove it if it failed.
            history = history.rsplit(f"USER: {user_input}\n", 1)[0]

if __name__ == "__main__":
    debug = "--debug" in sys.argv
    chat(debug)

# describe recursion with one sentence
# in italian
# in french
# with html formatting