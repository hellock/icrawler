from .base import BaseStorage
from .filesystem import FileSystem
try:
    from .google_storage import GoogleStorage
except ImportError as e:
    print('Google Cloud python API Missing')
    __all__ = ['BaseStorage','FileSystem']
    pass

__all__ = ['BaseStorage', 'FileSystem', 'GoogleStorage']
