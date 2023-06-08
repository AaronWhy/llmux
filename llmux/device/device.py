import inspect

class Device():
    def __init__(self, name, storage_dir = None, prompt='', load=True, save=True):
        """
        A device is an object that implements .help() and methods like .foo(*args, caller=None),
        where caller is a peer.
        Methods will be wrapped so the caller parameter is set to the peer that calls it.
        Methods can be either blocking or async, usually if it requests a backend.
        Device functions that does not start or end with '_' are exposed to peers.
        A device may have an internal non-volatile state.
        If save is True and has method save_, saves to storage on exit.
        If load is True and has method load_, tries loading from storage on start.
        """
        self.prompt = prompt
        self.code_snippet_length = 500
        self.name = name
        self.storage_dir = storage_dir
        self.save = save
        self.load = load

    def help(self, caller=None):
        """
        Automatically generates prompts for chatbots to explain devices and commands.
        """
        object = self
        doc = object.__doc__
        if doc is None:
            doc = '# Empty doctring' 
        else:
            doc = f'{self.name}.__doc__: {doc}'
        members = [item for item in dir(self) if not (item.startswith('_') or item.endswith('_'))]
        commands = ['Device commands include: ']
        for item in members:
            if callable(getattr(self, item)):
                commands.append(item)
        return f'Device name: {self.name}\n' + '\n'.join([self.prompt, doc] + commands) + '\n'
