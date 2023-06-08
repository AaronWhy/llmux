from ..level import LEVELS
class Handler():
    def __init__(self, peer, function, max_threads=1, on_event=[]):
        """
        A handler is in one of these states:
        an integer, sleep until that time since epoch
        runnable, will be scheduled by the system
        blocked, will not be scheduled
        """
        self.peer = peer
        self.function = function
        self.state = 'runnable'
        # execute the function again if an event is triggered
        self.on_event = on_event
        self.max_threads = max_threads
        self.tasks = []
        self.alertness = -1
        if 'always' in self.on_event:
            self.alertness = 10
        else:
            for item in self.on_event:
                if item in LEVELS:
                    self.alertness = max(self.alertness, LEVELS[item])

    async def handle(self, *args):
        # self.messages hold all events implicitly, handle them together, wait for the next one
        if not 'always' in self.on_event:
            self.state = 'blocked'
        result = await self.function(*args)
        return self.peer, result