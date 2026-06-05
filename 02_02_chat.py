#!/usr/bin/env python3
import sys
from utils import llm_generate, print_user, print_system, print_error, print_assistant

def chat(debug=False):
  # Llama 3.2 Chat tokens
  BEGIN = "<|begin_of_text|>"
  START_HEADER = "<|start_header_id|>"
  END_HEADER = "<|end_header_id|>\n\n"
  EOT = "<|eot_id|>"

  history = BEGIN
  # Optional: system message
  # history += f"{START_HEADER}system{END_HEADER}You are a helpful assistant.{EOT}"

  print("Chat with LLM (type 'exit' or 'quit' to stop)")

  while True:
    print_user("You: ", end="")
    user_input = input()
    if user_input.lower() in ['exit', 'quit']:
      break

    # Append user input to history with Llama 3 format
    history += f"{START_HEADER}user{END_HEADER}{user_input}{EOT}"

    try:
      assistant_response = llm_generate(history + f"{START_HEADER}assistant{END_HEADER}", debug)

      print_system("Assistant: ", end="")
      print_assistant(assistant_response)

      # Append assistant response to history
      history += f"{assistant_response}{EOT}"

    except Exception as e:
      print_error(f"Error: {e}")
      # Remove the last user message if it failed
      history = history.rsplit(f"{START_HEADER}user{END_HEADER}{user_input}{EOT}", 1)[0]

if __name__ == "__main__":
  debug = "--debug" in sys.argv
  chat(debug)
