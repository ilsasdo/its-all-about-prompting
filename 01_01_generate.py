#!/usr/bin/env python3
import sys
from utils import llm_generate, print_assistant


def main(debug=False):
    print("Welcome to 01_01_generate.py (type 'exit' or 'quit' to stop)")

    # NOTE: Loop on user input
    while True:
        try:
          user_input = input("Prompt: ")
          if user_input.lower() in ['exit', 'quit']:
            break
            
          if not user_input.strip():
              continue

          print_assistant(llm_generate(user_input, debug))

        except EOFError:
            break
        except KeyboardInterrupt:
            print("\nExiting...")
            break

if __name__ == "__main__":
    debug = "--debug" in sys.argv
    main(debug)
