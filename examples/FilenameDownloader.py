# based on example https://icrawler.readthedocs.io/en/latest/extend.html
from icrawler import ImageDownloader
from six.moves.urllib.parse import urlparse
import re

# https://stackoverflow.com/questions/1167617/in-python-how-do-i-indicate-im-overriding-a-method
def overrides(interface_class):
    def overrider(method):
        assert(method.__name__ in dir(interface_class))
        return method
    return overrider

class FilenameDownloader(ImageDownloader):

    @overrides(ImageDownloader)
    def get_filename(self, task, default_ext):

        url_path = urlparse(task["file_url"]).path
        file_name = url_path.split("/")[-1]

        if "." not in url_path:
            file_name = file_name + "." + default_ext

        file_name = file_name.replace(" ", "_")
        file_name = re.sub('[^a-zA-Z0-9_.]', '', file_name)

        return file_name
