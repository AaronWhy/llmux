import time
import re
from .user import User
from .peer import Peer
from ..prompt.prompt import format_prompt
from ..level import LEVELS

class Bot(Peer):
    def __init__(self, function, chatbot_backend, name, output_path=None, auto=False):
        """
        If auto is True, runs without user input, similar to 'continous mode' of AutoGPT.
        """
        self.function = function
        self.backend = chatbot_backend
        super().__init__(name, output_path, auto)
        self.task = None
        self.system_chat.broadcastMessage('system', f'Hi {self.name}, your task is {function}')

    def receiveMessage(self, sender, content, level=LEVELS['info']):
        """
        Prevent sending private messages to bots unless necessary.
        Broadcasting the message in a chat allows other bots, such as a critic to share information.
        """
        super().receiveMessage(sender, content, level)
        role = sender
        if isinstance(sender, Bot):
            # echo must be the same as raw content
            if sender is self:
                role = 'assistant'
            # message from another bot, set role = system to avoid confusion during generation
            else:
                role = 'system'
                content = f'{sender.name}: {content}'
        elif isinstance(sender, User):
            role = 'user'
            content = f'{sender.name}: {content}'
        else:
            assert sender == 'system'
        message = {'role': role, 'content': content}
        self.messages.append(message)
        self.file.write(f'{str(message)}\n')
        self.file.flush()

    def parseMessage(self, message):
        error_prompt = ''
        parsed = {}
        # find code snippets
        parsed['code'] = []
        # this is not general enough
        pattern = re.compile('(eval:\s*`(.+)`|exec:.*\\n?```([^`]+)```)')
        match = pattern.findall(message)
        for item in match:
            if len(item[1]) > 0:
                parsed['code'].append(('eval', item[1].strip()))
            elif len(item[2]) > 0:
                parsed['code'].append(('exec', item[2].strip()))
        # destination chat
        first_line = message[:message.find('\n')]
        if first_line[:2] == 'to' and ':' in first_line:
            first_line = first_line[2:]
            sep = first_line.find(':')
            chats = first_line[:sep].split(',')
            chats = [item.strip() for item in chats]
            parsed['to'] = chats
        elif len(parsed['code']) > 0:
            parsed['to'] = [self.system_chat.name]
        else:
            error_prompt = 'Wrong format.'
            error_prompt += format_prompt
        return message, parsed, error_prompt