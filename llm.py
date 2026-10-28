import os
from openai import OpenAI

base_url = 'https://api.groq.com/openai/v1'
model = 'openai/gpt-oss-20b'

client = OpenAI(base_url=base_url, api_key=os.environ['GROQ_API_KEY'])

def ask_llm(messages):
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0
    )
    return response.choices[0].message.content

if __name__ == '__main__':
    reply = ask_llm([
        {'role': 'system', 'content': 'Answer in one short sentence.'},
        {'role': 'user', 'content': 'What is phishing?'},
    ])
    print(reply)