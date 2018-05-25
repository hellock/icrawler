# -*- coding: utf-8 -*-

import os
import os.path as osp

import six

from icrawler.storage import BaseStorage


class FileSystem(BaseStorage):
    """Use filesystem as storage backend.

    The id is filename and data is stored as text files or binary files.
    """

    def __init__(self, root_dir):
        self.root_dir = root_dir

    def write(self, id, data):
        filepath = osp.join(self.root_dir, id)
        folder = osp.dirname(filepath)
        if not osp.isdir(folder):
            try:
                os.makedirs(folder)
            except OSError:
                pass
        mode = 'w' if isinstance(data, six.string_types) else 'wb'
        with open(filepath, mode) as fout:
            fout.write(data)

    def exists(self, id):
        return osp.exists(osp.join(self.root_dir, id))

    def max_file_idx(self):
        max_idx = 0
        for filename in os.listdir(self.root_dir):
            try:
                idx = int(osp.splitext(filename)[0])
            except ValueError:
                continue
            if idx > max_idx:
                max_idx = idx
        return max_idx
