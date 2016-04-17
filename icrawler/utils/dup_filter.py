# -*- coding: utf-8 -*-

import json


class DupFilter(object):
    """Filter duplicated urls or tasks.

    Use a dict to store most recent urls or tasks, each time a new item
    comes, check weather it has already been in the dict.

    Attributes:
        cache_size: An interger that controls the capacity of cache
                    (default 0, means unlimited capacity)
        cache_dict: A dict storing all the recent items
        cache_list: A list storing all the recent items in sequence order
    """

    def __init__(self, cache_size=0):
        """Init the DupFilter with specified cache capacity."""
        self.cache_size = cache_size
        self.cache_dict = {}
        self.cache_list = []

    def check_dup(self, elem):
        """Check whether the elem has been in the cache

        If the elem has not been seen before, then hash it and put it into
        the cache, otherwise indicates the elem is duplicated. When the cache
        size exceeds max capacity, discard the earliest elems in the cache.

        Args:
            elem: A dict or list or string to be checked.

        Returns:
            A boolean indicating if the elem has been seen recently.
        """
        if isinstance(elem, dict):
            hashable_item = json.dumps(elem, sort_keys=True)
        elif isinstance(elem, list):
            hashable_item = frozenset(elem)
        else:
            hashable_item = elem
        if hashable_item in self.cache_dict:
            return True
        else:
            self.cache_list.append(hashable_item)
            self.cache_dict[hashable_item] = 1
            if self.cache_size > 0 and len(self.cache_list) > self.cache_size:
                del self.cache_dict[self.cache_list.pop()]
            return False
