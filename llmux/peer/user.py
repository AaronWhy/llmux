from .peer import Peer
from ..backend import CLI
from ..level import LEVELS
from concurrent.futures import ThreadPoolExecutor

class User(Peer):
    def __init__(self, name):
        super().__init__(name, auto=True)

class CLIUser(User):
    def __init__(self, name, backend):
        self.chat_with = []
        super().__init__(name)
        self.backend = backend

    def joinChat(self, chat, say_hi=True):
        super().joinChat(chat, say_hi)
        self.chat_with = [chat.name]
        self.messages = f'{self.name} to {self.chat_with}: '

    def chatwith(self, name):
        self.chat_with = [name]
        self.messages = f'{self.name} to {self.chat_with}: '

    def parseMessage(self, message):
        """
        Instead of enforcing JSON, a CLI user may use a lightweight grammar.
        Start a line with an exclamation mark to eval a system call.
        ! self.chatwith("bot")
        to switch the current chat.
        """
        parsed = {'to': self.chat_with}
        if message[:2] == '! ':
            parsed['code'] = [('eval', message[2:])]
            parsed['to'] = [self.system_chat.name]
        message = f'to {", ".join(parsed["to"])}:' + message
        return message, parsed, ''

    def receiveMessage(self, sender, content, level=LEVELS['info']):
        super().receiveMessage(sender, content, level)
        if isinstance(sender, Peer):
            sender = sender.name
        if self.alertness > level:
            print(f'{sender}: {content}')