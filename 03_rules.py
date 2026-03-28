#!.venv/bin/python
from pathlib import Path
import sys
from utils import call_llm, print_token_usage, RESET, GRAY

def load_rules(rules_dir_path: str = "./rules") -> list:
    rules = []
    rules_dir = Path(rules_dir_path)
    if rules_dir.exists():
        for rule_file in sorted(rules_dir.glob("*.txt")):
            rule_content = rule_file.read_text().strip()
            if rule_content:
                rules.append({"role": "system", "content": rule_content})
    return rules

def chat(debug=False):
    history = load_rules()
    
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
            
            print_token_usage(response_data)
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
