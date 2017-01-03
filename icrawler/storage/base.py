from abc import ABCMeta, abstractmethod


class BaseStorage(metaclass=ABCMeta):
    """Base class of backend storage"""

    @abstractmethod
    def write(self, id, data):
        return

    @abstractmethod
    def max_file_idx(self):
        return 0
