# -*- coding: utf-8 -*-

from abc import ABCMeta, abstractmethod


class BaseStorage(object):
    """Base class of backend storage"""

    __metaclass__ = ABCMeta

    @abstractmethod
    def write(self, id, data):
        """Abstract interface of writing data

        Args:
            id (str): unique id of the data in the storage.
            data (bytes or str): data to be stored.
        """
        return

    @abstractmethod
    def exists(self, id):
        """Check the existence of some data

        Args:
            id (str): unique id of the data in the storage

        Returns:
            bool: whether the data exists
        """
        return False

    @abstractmethod
    def max_file_idx(self):
        """Get the max existing file index

        Returns:
            int: the max index
        """
        return 0
