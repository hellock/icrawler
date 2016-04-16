class Signal(object):

    def __init__(self):
        self.signals = {}
        self.init_status = {}

    def set(self, signals):
        for name in signals:
            if name not in self.signals:
                self.init_status[name] = signals[name]
            self.signals[name] = signals[name]

    def reset(self):
        self.signals = self.init_status

    def get(self, name):
        if name in self.signals:
            return self.signals[name]
        else:
            return None

    def names(self):
        return self.signals.keys()
