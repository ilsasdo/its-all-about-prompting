#!/usr/bin/env python3
import sys
from utils import llm_generate, print_assistant

# 1. llm_generate function -> https://docs.ollama.com/api/generate

if __name__ == "__main__":
    debug = "--debug" in sys.argv
    print_assistant(llm_generate('Explain in one sentence why Java is a better language than JavaScript. Make it a joke.', debug))
