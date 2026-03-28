#!.venv/bin/python
import sys
from utils import call_llm, print_token_usage

def generate(prompt, debug=False):
    response_data = call_llm(prompt, debug)
    print_token_usage(response_data)
    return response_data['response']

if __name__ == "__main__":
    debug = "--debug" in sys.argv
    print(generate("Explain recursion in one sentence.", debug))
