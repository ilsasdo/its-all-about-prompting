#!/usr/bin/env python3
import sys
from utils import llm_chat, print_user, print_system, print_error, print_assistant

def chat(debug=False):
    history = []
    
    print("Chat with LLM (type 'exit' or 'quit' to stop)")
    
    while True:
        print_user("You: ", end="")
        user_input = input()
        if user_input.lower() in ['exit', 'quit']:
            break
            
        # Append user input to history
        history.append({"role": "user", "content": user_input})
        
        try:
            response_data = llm_chat(history, debug=debug)
            assistant_response = response_data['message']['content']
            
            print_system("Assistant: ", end="")
            print_assistant(assistant_response)
            
            # Append assistant response to history
            history.append({"role": "assistant", "content": assistant_response})
            
        except Exception as e:
            print_error(f"Error: {e}")
            # Remove the last user message if it failed
            if history and history[-1]["role"] == "user":
                history.pop()

if __name__ == "__main__":
    debug = "--debug" in sys.argv
    chat(debug)
