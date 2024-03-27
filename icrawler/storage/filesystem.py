import os
import os.path as osp
import tempfile

import six

from .base import BaseStorage


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
        mode = "w" if isinstance(data, str) else "wb"
        # make sure file is saved, and try to name it correctly if possible
        # this avoids a race condition where the filename is available,
        # but another thread creates a file with the same name first.
        with tempfile.NamedTemporaryFile(mode, suffix="tmp", dir=folder, delete=False) as fout:
            fout.write(data)
        try:
            os.rename(fout.name, filepath)
        except:
            # possibly try to add characters to make a unique filename
            # until rename() succeeds
            pass

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
