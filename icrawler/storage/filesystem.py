import logging
import os
import os.path as osp

import six

from .base import BaseStorage

from io import BytesIO
from PIL import Image
from PIL.ExifTags import TAGS
import piexif


def read_EXIF(image_path):
    try:
        image = Image.open(image_path)
        exif_data = image.getexif()
        exif = ''
        for tag_id, value in exif_data.items():
            tag_description = TAGS.get(tag_id, tag_id)
            if isinstance(value, bytes):
                value = value.decode(errors='replace')
            exif += f"{tag_description:20}: {value}\n"
        return exif

    except Exception as e:
        return e


class FileSystem(BaseStorage):
    """Use filesystem as storage backend.

    The id is filename and data is stored as text files or binary files.
    """

    def __init__(self, root_dir):
        self.root_dir = root_dir

    def PIL_image_save(self, id, data):
        """
        For download images with metadata
        Image title (ImageDescription) = original image filename
        Author (Artist) = image url
        """
        image = Image.open(BytesIO(data.content))
        exif_dict = image.info.get('exif')
        if exif_dict:
            exif_dict = piexif.load(exif_dict)
        else:
            exif_dict = {"0th": {}, "Exif": {}, "GPS": {}, "Interop": {}, "1st": {}, "thumbnail": None}
        exif_dict['0th'][piexif.ImageIFD.Artist] = data.url.encode('utf-8')
        exif_dict['0th'][piexif.ImageIFD.ImageDescription] = data.url.split('/')[-1].encode('utf-8')
        exif_bytes = piexif.dump(exif_dict)

        filepath = osp.join(self.root_dir, id)
        folder = osp.dirname(filepath)
        if not osp.isdir(folder):
            try:
                os.makedirs(folder)
            except OSError:
                pass
        image.save(filepath, exif=exif_bytes)
        print(f"{read_EXIF(filepath)}")

    def write(self, id, data):
        filepath = osp.join(self.root_dir, id)
        folder = osp.dirname(filepath)
        if not osp.isdir(folder):
            try:
                os.makedirs(folder)
            except OSError:
                pass
        mode = "w" if isinstance(data, str) else "wb"
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
