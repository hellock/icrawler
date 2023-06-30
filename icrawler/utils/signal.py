class Signal:
    """Signal class

    Provides interfaces for set and get some globally shared variables(signals).

    Attributes:
        signals: A dict of all signal names and values.
        init_status: The initial values of all signals.
    """

    def __init__(self):
        """Init Signal with empty dicts"""
        self._signals = {}
        self._init_status = {}

    def set(self, **signals):
        """Set signals.

        Args:
            signals: A dict(key-value pairs) of all signals. For example
                     {'signal1': True, 'signal2': 10}
        """
        for name in signals:
            if name not in self._signals:
                self._init_status[name] = signals[name]
            self._signals[name] = signals[name]

    def reset(self):
        """Reset signals with their initial values"""
        self._signals = self._init_status.copy()

    def get(self, name):
        """Get a signal value by its name.

        Args:
            name: a string indicating the signal name.

        Returns:
            Value of the signal or None if the name is invalid.
        """
        if name in self._signals:
            return self._signals[name]
        else:
            return None

    def names(self):
        """Return all the signal names"""
        return self._signals.keys()
