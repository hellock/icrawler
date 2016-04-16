# -*- coding: utf-8 -*-

import json


class DupFilter(object):

    def __init__(self, cache_size=0):
        self.cache_size = cache_size
        self.cache_dict = {}
        self.cache_list = []

    def check_dup(self, elem):
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
