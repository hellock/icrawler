from google.cloud import storage

from icrawler.storage import BaseStorage
from io import BytesIO

class GSFileSystem(BaseStorage):
    """
       Use Google Storage file system as storage backend.
       The id is filename and data is stored as text files or binary files
       The root_dir is the bucket google storage address and will be parsed.
    """

    def __init__(self, root_dir):
        self.client = storage.Client()
        bucket_str = root_dir[5:].split('/')[0]
        self.bucket = self.client.get_bucket(bucket_str)
        self.folder_str = root_dir[5+len(bucket_str)+1:]
        if self.folder_str[0] == '/':
            self.folder_str = self.folder_str[1:]

    def write(self, id, data):
        blob = self.bucket.blob(self.folder_str + '/' + id)
        data_buffer = BytesIO(data)
        blob.upload_from_file(file_obj=data_buffer,
                              size=len(data))

    def max_file_idx(self):
        return len(self.bucket.list_blobs(prefix=self.folder_str))

