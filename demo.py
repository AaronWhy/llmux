import os
import asyncio

from llmux.system import System
from llmux.peer import CLIUser, Bot
from llmux.chat import Chat
from llmux.backend import OpenAIChatBot, OpenAIEmbedding, CLI
from llmux.device import LongtermMemory
from llmux.prompt import *
from llmux.handler import Recall

async def main():
    system = System()

    # ==== Backends ====
    api_type = os.environ.get('OPENAI_API_TYPE', 'open_ai')
    api_key = os.environ.get('OPENAI_API_KEY', None)
    api_base = os.environ.get('OPENAI_API_BASE', None)
    api_version = os.environ.get('OPENAI_API_VERSION', None)
    if api_key is None:
        print('Please set the environment variable "OPENAI_API_KEY".')
        exit()
    if api_type == 'open_ai':
        api_base = 'https://api.openai.com/v1'
    elif api_type == 'azure':
        api_version = '2023-03-15-preview'
    gpt4 = {'name': 'GPT4', 'description': 
            '''
            The most powerful chatbot available. 
            It is relatively expensive and the quota is limited, 
            so only call it for difficult problems that other chatbots cannot solve, 
            such as understanding and writing programs.
            ''',
            'api_key': api_key,
            'api_type': api_type,
            'api_version': api_version,
            'api_base': api_base,
            'model_name': 'gpt-4-32k', 
            'period_limit': 20}
    gpt4 = OpenAIChatBot(**gpt4)
    cli = CLI()
    system.chatbot_backends = {gpt4.name: gpt4}
    embedder = {'name': 'embedder', 'description': "",
            'api_key': api_key,
            'api_base': api_base,
            'api_type': api_type,
            'api_version': api_version,
            'period_limit': 20}
    embedding_backend = OpenAIEmbedding(**embedder)
    system.embedding_backends = {embedding_backend.name: embedding_backend}
    system.backends = system.chatbot_backends.copy()
    system.backends.update(system.embedding_backends)

    # ==== Devices ====
    storage_path = "/home/ubuntu/llmux_storage"
    output_path = "/home/ubuntu/llmux_output"
    system.storage_path = storage_path
    system.output_path = output_path
    note = LongtermMemory(embedding_backend, storage_path, name='note')
    devices = [note]
    for device in devices:
        system.addDevice(device)

    # ==== Users ====
    user = CLIUser('user', backend=cli)
    system.addUser(user)

    # ==== Bots ====
    additional_prompt = ""
    # energy saving
    main_function = "Enter inactive mode to save energy."
    additional_prompt = economy_principle
    # writing scripts
    # main_function = "Write a script to compute all prime numbers less than 50."
    # active skill acquiring
    # main_function = 'The "Phantom Veil" is a moth with deceptive protective coloration. Learn from the user how to find and catch it.'
    # additional_prompt = note.help()
    # Go to the forests on a summer night. Use ultra violet lights to attract the moth and use a net to catch them.
    # skill recall
    # main_function = 'Tell me how to catch a "Phantom Veil" moth.'
    # create another bot, remove it once it finishs
    # main_function = "Create a bot to compute all prime numbers less than 50."
    # additional_prompt = bot_prompt
    bot = Bot(main_function, gpt4, 'main_bot', output_path, auto=True)
    bot.handlers.append(Recall(bot.loginDevice(note), peer=bot, on_event=['info'], threshold=0.6))
    system.addBot(bot)

    # ==== Chats ====
    chat = Chat('main_chat', output_path)
    system.addChat(chat)
    user.joinChat(chat, say_hi=False)
    bot.joinChat(chat)

    # ====  Launch event loop ====
    if len(additional_prompt) > 0:
        bot.receiveMessage('system', additional_prompt)
    bot.receiveMessage(user, main_function)
    await system.eventLoop_()

if __name__ == '__main__':
    asyncio.run(main())