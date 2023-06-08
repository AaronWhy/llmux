import os
import copy
from pathlib import Path
import time
from datetime import datetime
from ..chat import Chat
from ..prompt import format_prompt
from ..handler import Handler
from ..level import LEVELS

class Peer():
    def __init__(self, name, output_path=None, auto=False, alertness='trivia'):
        self.name = name
        self.chats = {}
        self.messages = []
        self.output_path = output_path
        self.auto = auto
        self.file = None
        self.system = None
        if auto:
            on_event = ['always']
        else:
            on_event = ['receive_message']
        self.handlers = [Handler(self, self.requestMessage, 1, on_event)]
        if not output_path is None:
            Path(output_path).mkdir(parents=True, exist_ok=True)
            self.file = open(os.path.join(output_path, f'bot_{name}.txt'), "w")
        self.setAlterness(alertness)

        self.system_chat = Chat(f'{self.name}-system', output_path)
        self.joinChat(self.system_chat, say_hi=False)

    def setAlterness(self, alertness):
        if isinstance(alertness, str):
            alertness = LEVELS[alertness]
        self.alertness = alertness

    def sleep(self, n):
        self.setAlterness('info')
        wakeup_time = time.time() + n
        for handler in self.handlers:
            handler.state = wakeup_time
        return f'{self.name} sleeps until {datetime.fromtimestamp(wakeup_time)}.'

    def joinChat(self, chat, say_hi=True):
        self.chats[chat.name] = chat
        chat.peers[self.name] = self
        chat.broadcastMessage('system', f'{self.name} joined chat {chat.name}.')
        content = f'Hi {self.name}, you just joined a chat with {[name for name in chat.peers if not name==self.name]}. '
        if say_hi:
            content += ' Say hi and introduce yourself.'
        self.receiveMessage('system', content)

    def quitChat(self, chat_name):
        chat = self.chats.pop(chat_name)
        chat.peers.pop(self.name)

    def loginDevice(self, device):
        device = copy.copy(device)
        def decorator(func):
            def wrapper(*args, **kwargs):
                return func(caller = self, *args, **kwargs)
            wrapper.__doc__ = func.__doc__
            return wrapper
        members = [item for item in dir(device) if not (item.startswith('_') or item.endswith('_'))]
        for item in members:
            member = getattr(device, item)
            if callable(member):
                setattr(device, item, decorator(member))
        return device
    
    def __sendMessage(self, message, parsed, error_prompt):
        """
        Users and bots may use different message formats and parseMessage methods.
        But they can share the same sendMessage method.
        """
        valid_chats = []
        if len(error_prompt) == 0:
            if 'to' in parsed:
                chats = parsed['to']
                for chat_name in chats:
                    if chat_name in self.chats:
                        # do not directly broadcast a message, or a bot may receive it multiple times. 
                        self.chats[chat_name].dumpMessage(self.name, message)
                        valid_chats.append(self.chats[chat_name])
                    else:
                        error_prompt += f'"{chat_name}", '
                if len(error_prompt) > 0:
                    error_prompt = error_prompt[:-2]
                    error_prompt = "You cannot send message to these chats: " + error_prompt + ". "
        if len(error_prompt) > 0:
            error_prompt += "You have joined these chats: "
            for name, chat in self.chats.items():
                error_prompt += f'"{name}", '
            error_prompt = error_prompt[:-2]
            error_prompt += "."
            # invalid chats, forward message to system
            if len(error_prompt) > 0:
                self.system_chat.broadcastMessage(self, message)
                self.system_chat.broadcastMessage('system', error_prompt)
        
        # find the receivers and send message
        # each bot only receives message once, possibly from how multiple chats
        receivers = {}
        for chat in valid_chats:
            for name, peer in chat.peers.items():
                if not peer in receivers:
                    receivers[peer] = [chat]
                else:
                    receivers[peer].append(chat)
        for receiver, chats in receivers.items():
            receiver.receiveMessage(self, message)

    def sendMessage(self, message):
        content, parsed, error = self.parseMessage(message)
        self.__sendMessage(content, parsed, error)
        return parsed

    async def requestMessage(self):
        content = await self.backend.asyncRequest(self, self.messages)
        parsed = self.sendMessage(content)
        # sucessful parsing
        if isinstance(parsed, dict):
            # A system call is made
            if 'code' in parsed:
                for method, code in parsed['code']:
                    if method == 'eval':
                        content, level = self.system._eval(code, self)
                    elif method == 'exec':
                        content, level = self.system._exec(code, self)
                    if not content is None:
                        self.system_chat.broadcastMessage('system', content, level=level)
    
    def receiveMessage(self, sender, message, level=LEVELS['info']):
        # call handlers if the message is important enough
        if self.alertness >= level:
            for handler in self.handlers:
                if handler.alertness >= level:
                    handler.state = 'runnable'