import os
import json
from openai import OpenAI

base_url = 'https://api.groq.com/openai/v1'
model = 'openai/gpt-oss-20b'

client = OpenAI(base_url=base_url, api_key=os.environ['GROQ_API_KEY'])

def ask_llm(messages, json_mode=False):
    kwargs = {}
    if json_mode:
        kwargs['response_format'] = {'type': 'json_object'}
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0,
        **kwargs,  # extra args if there are
    )
    return response.choices[0].message.content

def parse_json(text):
    try:
        return json.loads(text)
    except json.JSONDecodeError as err:
        raise ValueError(f'Invalid JSON response: {text}') from err
def ask_json(messages):
    return parse_json(ask_llm(messages, json_mode=True))
def ask_with_tools(messages, tools):
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0,
        tools=tools,
    )
    return response.choices[0].message  # whole msg
if __name__ == '__main__':
    result = ask_json([
        {'role': 'system', 'content':
            'Extract fields from email headers. '
            'Reply with JSON only: '
            '{"from_domain": str, "reply_to_domain": str, "match": bool}'},
        {'role': 'user', 'content':
            'From: PayPal <service@paypal.com>\n'
            'Reply-To: help@secure-paypa1.net'},
    ])
    print(result)
    print(type(result))