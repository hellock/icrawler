# -*- coding: utf-8 -*-

from abc import ABCMeta, abstractmethod


class BaseStorage(metaclass=ABCMeta):
    """Base class of backend storage"""

    @abstractmethod
    def write(self, id, data):
        """Abstract interface of writing data

        Args:
            id (str): unique id of the data in the storage.
            data (bytes or str): data to be stored.
        """
        return

    @abstractmethod
    def max_file_idx(self):
        """Get the max existing file index

        Returns:
            int: the max index
        """
        return 0
