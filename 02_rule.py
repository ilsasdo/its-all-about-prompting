#!.venv/bin/python
import requests
from pathlib import Path

def read_rule():
    return Path("02_rule.txt").read_text()

def read_rule_2():
    return Path("02_rule_2.txt").read_text()

def read_rules():
    return "\n".join([read_rule(), read_rule_2()])

def generate(prompt):
    r = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": "llama3.2",
            "prompt": prompt,
            "stream": False
        }
    )
    return r.json()['response']

print(generate(read_rules() + "\nWrite a java test class that verifies a sum function"))