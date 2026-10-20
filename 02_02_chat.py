#!/usr/bin/env python3
import sys
from utils import llm_generate, print_user, print_system, print_error, print_assistant

# We are building a prompt with special tokens

# From https://dev.meta.ai/llama/docs/model-cards-and-prompt-formats/meta-llama-3
# <|begin_of_text|>: This is equivalent to the BOS token
# <|eot_id|>: This signifies the end of the message in a turn.
# <|start_header_id|>{role}<|end_header_id|>: These tokens enclose the role for a particular message. The possible roles can be: system, user, assistant.
# <|end_of_text|>: This is equivalent to the EOS token. On generating this token, Llama 3 will cease to generate more tokens.
# A prompt can optionally contain a single system message, or multiple alternating user and assistant messages, but always ends with the last user message followed by the assistant header.

def serialize_history(history: list[dict[str, str]]) -> str:
  prompt = "<|begin_of_text|>"
  for message in history:
    prompt += (
      f"<|start_header_id|>{message['role']}<|end_header_id|>\n\n"
      f"{message['content']}<|eot_id|>"
    )
  # NOTE: The prompt must end with the last user message followed by the assistant header.
  return prompt + "<|start_header_id|>assistant<|end_header_id|>\n\n"

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
      # NOTE: "raw=True"
      assistant_response = llm_generate(serialize_history(history), raw=True, debug=debug)

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
