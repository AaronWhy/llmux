import openai
from .backend import Backend

class ChatBot(Backend):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

class OpenAIChatBot(ChatBot):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def _setup(self):
        openai.api_type = self.api_type
        openai.api_version = self.api_version
        openai.api_base = self.api_base
        openai.api_key = self.api_key
        return openai

    def _call(self, messages):
        if self.api_type == 'azure':
            response = openai.ChatCompletion.create(
            engine=self.model_name,
            messages=messages,
            temperature=self.temperature,
            n=1
            )
            content = response['choices'][0]['message']['content']
            return content
        elif self.api_type == 'open_ai':
            response = openai.ChatCompletion.create(
                model=self.model_name,
                messages=messages,
                temperature=self.temperature,
                n=1
            )
            content = response['choices'][0]['message']['content']
        else:
            assert False
        return content