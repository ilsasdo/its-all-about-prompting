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
    
    print("Chat with LLM (type 'exit' or 'quit' to stop, '/plan' to generate a plan, '/summarize' to summarize chat)")
    
    PLAN_PROMPT = """Analyze the task and provide a detailed step-by-step plan for its execution.
Identify potential risks, dependencies, and key milestones.
Format the output as a numbered list with clear explanations for each step."""

    SUMMARIZE_PROMPT = """Summarize the current chat history into a concise yet detailed summary.
Retain the most relevant information and current task context.
The summary will be used to reduce the context size, so it must capture the essence of the entire conversation."""

    while True:
        print_user("You: ", end="")
        user_input = input()
        if user_input.lower() in ['exit', 'quit']:
            break
            
        is_summarize = False
        if user_input.strip().lower() == '/plan':
            history.append({"role": "user", "content": PLAN_PROMPT})
        elif user_input.strip().lower() == '/summarize':
            history.append({"role": "user", "content": SUMMARIZE_PROMPT})
            is_summarize = True
        else:
            # Append user input to history
            history.append({"role": "user", "content": user_input})
        
        try:
            response_data = llm_chat(history, debug=debug)
            assistant_response = response_data['message']['content']
            
            print_system("Assistant: ", end="")
            print_assistant(assistant_response)
            
            if is_summarize:
                # Replace history with the summary while keeping rules
                history = load_rules()
                history.append({"role": "assistant", "content": f"Summary of previous chat history:\n{assistant_response}"})
            else:
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

# chats:
# I want to build a simple chess engine in python. what should I do?