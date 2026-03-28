#!.venv/bin/python
import sys
from utils import call_llm, print_token_usage, RESET, GRAY

def chat(debug=False):
    # Llama 3.2 Chat tokens
    BEGIN = "<|begin_of_text|>"
    START_HEADER = "<|start_header_id|>"
    END_HEADER = "<|end_header_id|>\n\n"
    EOT = "<|eot_id|>"
    
    history = BEGIN
    # Optional: system message
    # history += f"{START_HEADER}system{END_HEADER}You are a helpful assistant.{EOT}"
    
    # ANSI color codes
    BLACK = "\033[30m"
    GREEN = "\033[32m"
    
    print("Chat with LLM (type 'exit' or 'quit' to stop)")
    
    while True:
        user_input = input(f"{BLACK}You: ")
        print(RESET, end="")
        if user_input.lower() in ['exit', 'quit']:
            break
            
        # Append user input to history with Llama 3 format
        history += f"{START_HEADER}user{END_HEADER}{user_input}{EOT}"
        
        try:
            response_data = call_llm(history + f"{START_HEADER}assistant{END_HEADER}", debug)
            assistant_response = response_data['response']
            
            print_token_usage(response_data)
            print(f"{GREEN}Assistant: {assistant_response}{RESET}")
            
            # Append assistant response to history
            history += f"{assistant_response}{EOT}"
            
        except Exception as e:
            print(f"Error: {e}")
            # Remove the last user message if it failed
            history = history.rsplit(f"{START_HEADER}user{END_HEADER}{user_input}{EOT}", 1)[0]

if __name__ == "__main__":
    debug = "--debug" in sys.argv
    chat(debug)
