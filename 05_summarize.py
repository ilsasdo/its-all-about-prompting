#!/usr/bin/env python3
from pathlib import Path
import sys
from utils import llm_generate, print_user, print_system, print_error, print_assistant

# Load rules from filesystem
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

def serialize_history(history: list[dict[str, str]]) -> str:
    prompt = "<|begin_of_text|>"
    for message in history:
        prompt += (
            f"<|start_header_id|>{message['role']}<|end_header_id|>\n\n"
            f"{message['content']}<|eot_id|>"
        )
    return prompt + "<|start_header_id|>assistant<|end_header_id|>\n\n"

def chat(debug=False):
    history = load_rules()
    
    print("Chat with LLM (type 'exit' or 'quit' to stop, '/plan' to generate a plan, '/summarize' to summarize chat)")

    plan_prompt = """Analyze the task and provide a detailed step-by-step plan for its execution.
    Identify potential risks, dependencies, and key milestones.
    Format the output as a numbered list with clear explanations for each step."""

    summarize_prompt = """Summarize the current chat history into a concise yet detailed summary.
Retain the most relevant information and current task context.
The summary will be used to reduce the context size, so it must capture the essence of the entire conversation."""

    while True:
        print_user("You: ", end="")
        user_input = input()
        if user_input.lower() in ['exit', 'quit']:
            break
            
        is_summarize = user_input.strip().lower() == '/summarize'
        if is_summarize:
            history.append({"role": "user", "content": summarize_prompt})
        else:
            if user_input.strip().lower().startswith('/plan'):
                history.append({"role": "user", "content": f"{plan_prompt}\n{user_input}"})
            else:
                # Append user input to history
                history.append({"role": "user", "content": user_input})
        
        try:
            assistant_response = llm_generate(serialize_history(history), raw=True, debug=debug)

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
