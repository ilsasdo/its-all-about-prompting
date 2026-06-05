#!/usr/bin/env python3
from pathlib import Path
import sys
from utils import llm_chat, print_user, print_system, print_error, print_assistant

def load_rules(rules_dir_path: str = "./rules") -> list:
    rules_content = ["Follow these rules:"]
    rules_dir = Path(rules_dir_path)
    if rules_dir.exists():
        for rule_file in sorted(rules_dir.glob("*.txt")):
            content = rule_file.read_text().strip()
            if content:
                rules_content.append(content)
    
    if len(rules_content) > 1:
        full_rules = "\n".join(rules_content)
        return [{"role": "system", "content": full_rules}]
    return []

def chat(debug=False):
    history = load_rules()
    
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
