#!.venv/bin/python
import sys
from utils import llm_generate, print_assistant

if __name__ == "__main__":
    debug = "--debug" in sys.argv
    print_assistant(llm_generate('Explain recursion in one sentence.', debug))
