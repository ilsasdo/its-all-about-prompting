#!/usr/bin/env python3
import sys
from utils import llm_generate, print_user, print_system, print_error, print_assistant

def chat(debug=False):
  history = ""

  print("Chat with LLM (type 'exit' or 'quit' to stop)")

  while True:
    print_user("You: ", end="")
    user_input = input()
    if user_input.lower() in ['exit', 'quit']:
      break

    # Append user input to history with USER: prefix
    history += f"USER: {user_input}\n"

    try:
      assistant_response = llm_generate(history + "SYSTEM: ", debug)

      print_system("Assistant: ", end="")
      print_assistant(assistant_response)

      # Append assistant response to history with SYSTEM: prefix
      history += f"SYSTEM: {assistant_response}\n"

    except Exception as e:
      print_error(f"Error: {e}")
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