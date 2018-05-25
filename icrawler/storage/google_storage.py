from icrawler.storage import BaseStorage
from io import BytesIO


class GoogleStorage(BaseStorage):
    """Google Storage backend.

    The id is filename and data is stored as text files or binary files.
    The root_dir is the bucket address such as gs://<your_bucket>/<your_directory>.
    """

    def __init__(self, root_dir):
        try:
            from google.cloud import storage
        except ImportError:
            print('GoogleStorage backend requires the package '
                  '"google-cloud-storage", execute '
                  '"pip install google-cloud-storage" to install it.')

        self.client = storage.Client()
        bucket_str = root_dir[5:].split('/')[0]
        self.bucket = self.client.get_bucket(bucket_str)
        self.folder_str = root_dir[6 + len(bucket_str):]
        if self.folder_str[0] == '/':
            self.folder_str = self.folder_str[1:]

    def write(self, id, data):
        blob = self.bucket.blob(self.folder_str + '/' + id)
        data_buffer = BytesIO(data)
        blob.upload_from_file(file_obj=data_buffer, size=len(data))

    def exists(self, id):
        blob = self.bucket.blob(self.folder_str + '/' + id)
        return blob.exists()

    def max_file_idx(self):
        return len(self.bucket.list_blobs(prefix=self.folder_str))
