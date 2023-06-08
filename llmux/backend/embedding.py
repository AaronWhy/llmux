import openai
from .backend import Backend

class OpenAIEmbedding(Backend):
    def __init__(self, **kwargs):
        kwargs['model_name'] = 'text-embedding-ada-002' 
        kwargs['description'] = 'computes vector embedding of text.' 
        kwargs['name'] = 'text_embedder' 
        super().__init__(**kwargs)
        self.dim = 1536

    def _setup(self):
        openai.api_type = self.api_type
        openai.api_version = self.api_version
        openai.api_base = self.api_base
        openai.api_key = self.api_key
        return openai

    def _call(self, text):
        # No longer necessary to replace \n, refer to https://github.com/openai/openai-python/issues/418
        #text = text.replace("\n", " ")
        if self.api_type == 'open_ai':
            return openai.Embedding.create(input = [text], model=self.model_name)['data'][0]['embedding']
        elif self.api_type == 'azure':
            return openai.Embedding.create(input = [text], engine=self.model_name)['data'][0]['embedding']
        else:
            assert False