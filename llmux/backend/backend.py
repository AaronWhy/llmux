import asyncio
import time  
import traceback  
from concurrent.futures import ThreadPoolExecutor
import heapq
from ..device import Device

class Request():
    def __init__(self, caller, content):
        self.content = content
        self.caller = caller
        # future: set priority according to the caller
        self.priority = 0

    def __lt__(self, other):
        # smaller is higher
        return self.priority < other.priority

class Backend(Device):
    def __init__(self, name, description, api_type=None, api_key=None, api_version=None, api_base=None,
                  model_name=None, period_limit=0, temperature=0.6, timeout=60):
        """
        A backend is a device that forward requests away from llmux (e.g. to an LLM inference server).
        period_limit: wait at least so many seconds before calling the API again, 
        since the server may refuse frequent requiests.
        """
        self.name = name
        self.description = description
        self.api_type = api_type
        self.api_version = api_version
        self.api_key = api_key
        self.api_base = api_base
        self.model_name = model_name
        self.temperature = temperature
        self.period_limit = period_limit
        self.last_call = 0
        self.timeout = timeout
        self.queue = []
        heapq.heapify(self.queue)
        self.task = None

    def _setup(self):
        pass

    async def asyncRequest(self, caller, content):
        request = Request(caller, content)
        heapq.heappush(self.queue, request)
        while not self.queue[0] == request:
            await asyncio.sleep(0.2)
        request = heapq.heappop(self.queue)
        caller, content = request.caller, request.content
        success = False
        while not success:
            # Do not send requests too often
            cur_time = time.time()
            if cur_time - self.last_call < self.period_limit:
                await asyncio.sleep(self.period_limit - cur_time + self.last_call)
            self.last_call = time.time()
            # Notice _setup() may be multithread unsafe, improvements needed
            self._setup()
            try:
                with ThreadPoolExecutor(1) as executor:
                    content = await asyncio.get_event_loop().run_in_executor(executor, self._call, content)
                    success = True
            except BaseException as e:
                print(f'Backend {self.name} call failed {traceback.format_exc()}')
                print('Retrying.')
        return content

    def request(self, caller, content):
        request = Request(caller, content)
        heapq.heappush(self.queue, request)
        while not self.queue[0] == request:
            time.sleep(0.2)
        request = heapq.heappop(self.queue)
        caller, content = request.caller, request.content
        success = False
        while not success:
            # Do not send requests too often
            cur_time = time.time()
            if cur_time - self.last_call < self.period_limit:
                time.sleep(self.period_limit - cur_time + self.last_call)
            self.last_call = time.time()
            # Notice _setup() may be multithread unsafe, improvements needed
            self._setup()
            try:
                content = self._call(content)
                success = True
            except BaseException as e:
                print(f'Backend {self.name} call failed {traceback.format_exc()}')
                print('Retrying.')
        return content