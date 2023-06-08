from .backend import Backend

class CLI(Backend):
    def __init__(self, **kwargs):
        """
        period_limit: wait at least so many seconds before calling the API again, 
        since the server may refuse frequent requiests.
        """
        kwargs['name'] = 'command_line_interface'
        kwargs['description'] = 'backend for user keyboard input.'
        kwargs['timeout'] = int(1e8)
        super().__init__(**kwargs)

    def _call(self, messages):
        return input(messages)