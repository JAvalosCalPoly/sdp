import json
from llm import ask_with_tools, parse_json

def get_domain(address):
    domain = address.split('@')[-1]  # after last @
    return domain.strip().rstrip('>').lower()

# schema the model sees
GET_DOMAIN_SPEC = {
    'type': 'function',
    'function': {
        'name': 'get_domain',
        'description': 'Extract the domain from an email address.',
        'parameters': {
            'type': 'object',
            'properties': {
                'address': {'type': 'string', 'description': 'Email address'},
            },
            'required': ['address'],
        },
    },
}

class Agent:
    def __init__(self, system_prompt, tools, max_steps=5):
        self.system_prompt = system_prompt
        self.funcs = {name: f for name, (f, _) in tools.items()}  # name -> func
        self.specs = [spec for _, spec in tools.values()]          # for api
        self.max_steps = max_steps

    def run(self, user_input):
        messages = [
            {'role': 'system', 'content': self.system_prompt},
            {'role': 'user', 'content': user_input},
        ]
        for step in range(self.max_steps):
            msg = ask_with_tools(messages, self.specs)

            if not msg.tool_calls:
                print(f'step {step}: final')  # temp
                return parse_json(msg.content)  # done

            # echo model's request back
            messages.append({
                'role': 'assistant',
                'content': msg.content or '',
                'tool_calls': [
                    {'id': c.id, 'type': 'function',
                     'function': {'name': c.function.name,
                                  'arguments': c.function.arguments}}
                    for c in msg.tool_calls
                ],
            })

            for call in msg.tool_calls:
                name = call.function.name
                print(f'step {step}: {name}({call.function.arguments})')  # temp
                func = self.funcs.get(name)
                try:
                    args = json.loads(call.function.arguments)
                    result = func(**args) if func else f'Error: unknown tool {name!r}'
                except Exception as err:
                    result = f'Error: {err}'  # bad args etc
                messages.append({
                    'role': 'tool',
                    'tool_call_id': call.id,  # links result to call
                    'content': str(result),
                })

        raise RuntimeError('Agent hit max steps')  # no final

if __name__ == '__main__':
    prompt = (
        'You check if From and Reply-To domains match. '
        'Use get_domain on each address first. '
        'Then reply with JSON only: {"match": bool, "reason": str}'
    )
    agent = Agent(prompt, {'get_domain': (get_domain, GET_DOMAIN_SPEC)})
    print(agent.run(
        'From: PayPal <service@paypal.com>\n'
        'Reply-To: help@secure-paypa1.net'))