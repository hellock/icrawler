# -*- coding: utf-8 -*-

from os import listdir, makedirs, path

from icrawler.storage import BaseStorage


class FileSystem(BaseStorage):
    """Use filesystem as storage backend.

    The id is filename and data is stored as text files or binary files.
    """

    def __init__(self, root_dir):
        self.root_dir = root_dir

    def write(self, id, data):
        filepath = path.join(self.root_dir, id)
        folder = path.dirname(filepath)
        if not path.isdir(folder):
            try:
                makedirs(folder)
            except:
                pass
        mode = 'w' if isinstance(data, str) else 'wb'
        with open(filepath, mode) as fout:
            fout.write(data)

    def max_file_idx(self):
        max_idx = 0
        for filename in listdir(self.root_dir):
            try:
                idx = int(path.splitext(filename)[0])
            except:
                continue
            if idx > max_idx:
                max_idx = idx
        return max_idx
