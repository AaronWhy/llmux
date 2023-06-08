from .handler import Handler

class Recall(Handler):
    def __init__(self, database, k=3, threshold=0.4, **kwargs):
        """
        by default, only trigger when the memory is highly relevant
        the agent can increase the threshold and recall less relevant memory
        """
        kwargs['function'] = self.recall
        super().__init__(**kwargs)
        self.database = database
        self.threshold = threshold
        self.k = k
        self.cnt = 0

    async def recall(self):
        messages = self.peer.messages[self.cnt:]
        self.cnt = len(self.peer.messages)
        message = ''
        for item in messages:
            message += f'{item["role"]}: {item["content"]}\n'
        content = await self.database.asyncQuery(message, self.k)
        hits = []
        for distance, item in content:
            if distance < self.threshold:
                hits.append(item)
        if len(hits) > 0:
            content = f'Here are relevant records in your database "{self.database.name}":\n'
            for item in hits:
                content += f'{item}\n====\n'
            # do not trigger itself
            self.peer.system_chat.broadcastMessage('system', content, level = self.alertness+0.1)