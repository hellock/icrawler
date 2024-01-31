# based on example https://icrawler.readthedocs.io/en/latest/extend.html
# 
# set in Downloader::download()
# task["file_url"] = ""
# task["filename"] = Downloader::get_filename()
# task["success"] = True
# 
# task["img_size"] = img.size

from icrawler import ImageDownloader
from six.moves.urllib.parse import urlparse
from os import path
import re
import logging

import FileTypes

# https://stackoverflow.com/questions/1167617/in-python-how-do-i-indicate-im-overriding-a-method
def overrides(interface_class):
    def overrider(method):
        assert(method.__name__ in dir(interface_class))
        return method
    return overrider

class FilenameDownloader(ImageDownloader):

    @overrides(ImageDownloader)
    def __init__(self, thread_num, signal, session, storage):
        super().__init__(thread_num, signal, session, storage)
        self.filename_list = []

    @overrides(ImageDownloader)
    def keep_file(self, task, response, min_size=None, max_size=None):

        #if not super().keep_file(task, response, min_size, max_size):
        #    return False

        h = response.content[:32]
        extension = FileTypes.get_filetype(h)
        # TODO: identify these
        # TODO: use the original extension and log these at WARN or DEBUG level
        if extension is None:
            extension = "unk" 

        #  save filename from Content-Disposition if possible, otherwise from get_filename()
        disposition_magic = "Content-Disposition"
        if disposition_magic in response.headers:
            disposition = response.headers[disposition_magic]
            filename = disposition.split("filename=")[-1]
            # ex: "disposition: inline; filename="Kentucky2015.jpg"; filename*=UTF-8''Kentucky2015.jpg"
            filename = filename.split(";")[0]
            if filename[0] == '"' and filename[-1] == '"':
                filename = filename[1:len(filename)-1]
        else:
            filename = self.get_filename(task, extension)

        (filename, ext) = path.splitext(filename)

        # this is not thread safe, it's at least a little better tho
        tempname = filename
        for ix in range(1000):
            if tempname + "." + extension not in self.filename_list:
                filename = tempname
                break
            tempname = f"{filename}{ix:03d}"

        self.filename_list.append(filename + "." + extension)

        task["filename"] = filename
        task["filetype"] = extension

        # TODO: mime sniffing here if needed "Content-Type":
        # attempt to revert downloader.py

        return True

    @overrides(ImageDownloader)
    def get_filename(self, task, default_ext):
        max_length = 240
        if task["filename"]:
            if task["filetype"]:
                filename = task["filename"][:max_length] + "." + task["filetype"]
            else:
                filename = task["filename"][:max_length]
        else:
            url_path = urlparse(task["file_url"]).path
            filename = url_path.split("/")[-1]

            if "." not in filename and default_ext:
                filename = filename[:max_length-1-len(default_ext)] + "." + default_ext

            filename = filename.replace(" ", "_")
            filename = re.sub("[^a-zA-Z0-9_.-]", "", filename)

            if len(filename) > max_length:
                (filename, ext) = path.splitext(filename)
                filename = filename[:max_length-1-len(ext)] + "." + ext

        return filename
