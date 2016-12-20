from .google import GoogleImageCrawler
from .bing import BingImageCrawler
from .baidu import BaiduImageCrawler
from .flickr import FlickrImageCrawler
from .greedy import GreedyImageCrawler
from .urllist import UrlListCrawler

# __all__ = ['google', 'bing', 'baidu', 'flickr', 'greedy', 'urllist']
__all__ = ['BaiduImageCrawler', 'BingImageCrawler', 'FlickrImageCrawler',
           'GoogleImageCrawler', 'GreedyImageCrawler', 'UrlListCrawler']
