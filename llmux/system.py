import time
import asyncio
import traceback
from .peer import Bot
from .backend import ChatBot
from .chat import Chat
# do not remove these "unused" imports, they are used via globals()
from .device import Device
from .prompt import global_prompt
from .level import LEVELS
from .util import ReturnValue

class System(Device):
    def __init__(self):
        super().__init__(name = 'system')
        self.bots = {}
        self.users = {}
        self.peers = {}
        self.chats = {}
        self.devices = {}
        self.chatbot_backends = {}
        self.embedding_backends = {}
        self.backends = {}

        self.globals = {'time': time, 'asyncio': asyncio, 'system': self}
        self.prompt = global_prompt

    def addBot(self, bot):
        """
        Create a bot to autonomously perform tasks.
        """
        self.bots[bot.name] = bot
        self.peers[bot.name] = bot
        bot.system = self
        bot.system_chat.broadcastMessage('system', self.prompt)
        device_prompt = 'Here is the list of devices available:\n'
        for name, device in self.devices.items():
            device_prompt  += f'{device.help()}\n'
        bot.system_chat.broadcastMessage('system', device_prompt)

    def removeBot(self, name):
        if name in self.bots:
            bot = self.bots.pop(name)
            self.peers.pop(name)
            for name, chat in bot.chats.items():
                chat.peers.pop(bot.name)
            if bot.file is not None:
                bot.file.close()
            for handler in bot.handlers:
                for task in handler.tasks:
                    task.cancel()
            return f"Removed bot named {name}"
        else:
            return "There is no such a bot."

    def addUser(self, user):
        user.system = self
        self.users[user.name] = user
        self.peers[user.name] = user

    def addChat(self, chat):
        if chat.name in self.chats:
            return "Chat name has been used. Try another name."
        else:
            self.chats[chat.name] = chat
            return f"Added chat named {chat.name}"

    def removeChat(self, chat_name):
        if chat_name in self.chats:
            chat = self.chats.pop(chat_name)
            for name, peer in chat.peers.copy().items():
                peer.quitChat(chat_name)
                if chat.file is not None:
                    chat.file.close()
            return f"Removed chat named {chat_name}"
        else:
            return "There is no such a chat."

    def addDevice(self, device):
        self.devices[device.name] = device
        self.globals.update(self.devices)
        device.load_()
        device_prompt = 'A new device is available. Here is its usage:\n'
        device_prompt  += f'{device.help()}\n'
        for peer in self.peers:
            peer.system_chat.broadcastMessage('system', device_prompt)

    def exit(self):
        self.finished = True
        chat_names = list(self.chats.keys())
        for name in chat_names:
            self.removeChat(name)
        bot_names = list(self.bots.keys())
        for name in bot_names:
            self.removeBot(name)
        for name, device in self.devices.items():
            if hasattr(device, 'save_') and device.save:
                device.save_()
        print('Released all resources, ready to exit.')

    def _eval(self, code, peer):
        tmp = globals().copy()
        tmp.update(self.globals)
        tmp['self'] = peer
        for name, device in self.devices.items():
            device = peer.loginDevice(device)
            tmp[name] = device
        try:
            return_value = eval(code, tmp)
            content = f"Call finished. The results are {return_value}"
            level = LEVELS['info']
        except BaseException as e:
            content = traceback.format_exc()
            level = LEVELS['error']
        return content, level

    def _exec(self, code, peer):
        tmp = globals().copy()
        tmp.update(self.globals)
        tmp['self'] = peer
        for name, device in self.devices.items():
            device = peer.loginDevice(device)
            tmp[name] = device
        returnValue = ReturnValue()
        tmp['returnValue'] = returnValue
        try:
            exec(code, tmp)
            result = returnValue.value
            if result is None:
                if 'return_value' in code:
                    content = 'system.exec return valu is None. If that is not what you expect, perhaps you redefined return_value by mistake.'
                    level = LEVELS['warn']
                else:
                    content = 'Script finished without return values.'
                    level = LEVELS['info'] - 0.5
            else:
                content = f"Script finished. The results are {result}"
                level = LEVELS['error']
        except BaseException as e:
            content = traceback.format_exc()
            level = LEVELS['error']
        return content, level

    async def eventLoop_(self):
        self.finished = False
        for device in self.devices:
            if hasattr(device, 'load_') and device.load:
                device.load_()
        while not self.finished:
            tasks = []
            # find runnable and running handlers
            for name, peer in self.peers.items():
                for handler in peer.handlers:
                    # wake up sleeping handlers
                    if isinstance(handler.state, float) and handler.state < time.time():
                        handler.state = 'runnable'
                    # schedule runnable handlers
                    if handler.state == 'runnable' and len(handler.tasks) < handler.max_threads:
                        task = asyncio.create_task(handler.handle())
                        handler.tasks.append(task)
                    tasks += handler.tasks
            # wait until any task finishs
            done, pending = await asyncio.wait(tasks, return_when = asyncio.FIRST_COMPLETED)
            # remove finished tasks
            for name, peer in self.peers.items():
                for handler in peer.handlers:
                    tasks = []
                    for task in handler.tasks:
                        if not task in done:
                            tasks.append(task)
                    handler.tasks = tasks    