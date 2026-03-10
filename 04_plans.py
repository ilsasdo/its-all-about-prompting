#!.venv/bin/python
import requests

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

print(generate("You need to build a plan"))
