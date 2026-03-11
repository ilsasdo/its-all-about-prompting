#!.venv/bin/python
import requests
from pathlib import Path

def load_rules(rules_dir_path: str = "./rules") -> list:
    rules = []
    rules_dir = Path(rules_dir_path)
    if rules_dir.exists():
        for rule_file in sorted(rules_dir.glob("*.txt")):
            rule_content = rule_file.read_text().strip()
            if rule_content:
                rules.append({"role": "system", "content": rule_content})
    return rules

def chat():
    url = "http://localhost:11434/api/chat"
    history = load_rules()
    
    # ANSI color codes
    BLACK = "\033[30m"
    GREEN = "\033[32m"
    GRAY = "\033[90m"
    RESET = "\033[0m"
    
    print("Chat with LLM (type 'exit' or 'quit' to stop, '/plan' to generate a plan, '/summarize' to summarize chat)")
    
    PLAN_PROMPT = """Analyze the task and provide a detailed step-by-step plan for its execution.
Identify potential risks, dependencies, and key milestones.
Format the output as a numbered list with clear explanations for each step."""

    SUMMARIZE_PROMPT = """Summarize the current chat history into a concise yet detailed summary.
Retain the most relevant information and current task context.
The summary will be used to reduce the context size, so it must capture the essence of the entire conversation."""

    while True:
        user_input = input(f"{BLACK}You: ")
        print(RESET, end="")
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
            r = requests.post(
                url,
                json={
                    "model": "llama3.2",
                    "messages": history,
                    "stream": False
                }
            )
            r.raise_for_status()
            response_data = r.json()
            assistant_response = response_data['message']['content']
            
            prompt_tokens = response_data.get('prompt_eval_count', 0)
            eval_tokens = response_data.get('eval_count', 0)
            print(f"{GRAY}[Prompt: {prompt_tokens}, Response: {eval_tokens}, Total: {prompt_tokens + eval_tokens}]{RESET}")
            print(f"{GREEN}Assistant: {assistant_response}{RESET}")
            
            if is_summarize:
                # Replace history with the summary while keeping rules
                history = load_rules()
                history.append({"role": "assistant", "content": f"Summary of previous chat history:\n{assistant_response}"})
            else:
                # Append assistant response to history
                history.append({"role": "assistant", "content": assistant_response})
            
        except Exception as e:
            print(f"Error: {e}")
            # Remove the last user message if it failed
            if history and history[-1]["role"] == "user":
                history.pop()

if __name__ == "__main__":
    chat()

# chats:
# I want to build a simple chess engine in python. what should I do?