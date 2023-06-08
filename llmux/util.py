class ReturnValue():
    def __init__(self):
        self.value = None
    def __call__(self, value):
        self.value = value