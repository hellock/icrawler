from os import listdir, makedirs, path

from icrawler.storage import BaseStorage


class FileSystem(BaseStorage):

    def __init__(self, root_dir):
        self.root_dir = root_dir

    def write(self, id, data):
        filepath = path.join(self.root_dir, id)
        folder = path.dirname(filepath)
        if not path.isdir(folder):
            makedirs(folder)
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
