from abc import ABCMeta, abstractmethod


class BaseStorage:
    """Base class of backend storage"""

    __metaclass__ = ABCMeta

    @abstractmethod
    def write(self, id, data):
        return

    @abstractmethod
    def max_file_idx(self):
        return 0
