import os
import time
from pathlib import Path
from .level import LEVELS

class Chat():
    def __init__(self, name, output_path=None):
        """
        A chat may have different names for different bots.
        """
        self.messages = []
        self.peers = {}
        self.name = name
        self.file = None
        if not output_path is None:
            Path(output_path).mkdir(parents=True, exist_ok=True)
            self.file = open(os.path.join(output_path, f'chat_{name}.txt'), "w")

    def broadcastMessage(self, sender, message, level=LEVELS['info']):
        """
        Broadcast messages to bots in this chat.
        """
        for name, peer in self.peers.items():
            for chat_name, chat  in peer.chats.items():
                if chat is self:
                    break
            peer.receiveMessage(sender, message, level)
        self.dumpMessage(sender, message)

    def dumpMessage(self, sender, content):
        """
        Record messages sent to this chat for debugging purpose.
        Chats logs are formatted for human readers, refer to bot logs the raw message that bots read.
        """
        if not isinstance(sender, str):
            sender = sender.name
        message = f"{sender}: {content}\n"
        self.messages.append(message)
        if not self.file is None:
            self.file.write(time.strftime("%Y-%m-%d %H:%M:%S\n", time.localtime()) )
            self.file.write(message)
            self.file.flush()