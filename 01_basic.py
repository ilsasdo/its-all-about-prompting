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
    response_data = r.json()
    prompt_tokens = response_data.get('prompt_eval_count', 0)
    eval_tokens = response_data.get('eval_count', 0)
    print(f"\033[90m[Prompt: {prompt_tokens}, Response: {eval_tokens}, Total: {prompt_tokens + eval_tokens}]\033[0m")
    return response_data['response']

print(generate("Explain recursion in one sentence."))
