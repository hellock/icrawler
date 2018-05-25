# -*- coding: utf-8 -*-

import json

from icrawler import Crawler, Feeder, Parser, ImageDownloader
from icrawler.builtin.filter import Filter


class BaiduFeeder(Feeder):

    def get_filter(self):
        search_filter = Filter()

        # type filter
        type_code = {
            'portrait': 's=3&lm=0&st=-1&face=0',
            'face': 's=0&lm=0&st=-1&face=1',
            'clipart': 's=0&lm=0&st=1&face=0',
            'linedrawing': 's=0&lm=0&st=2&face=0',
            'animated': 's=0&lm=6&st=-1&face=0',
            'static': 's=0&lm=7&st=-1&face=0'
        }

        def format_type(img_type):
            return type_code[img_type]

        type_choices = list(type_code.keys())
        search_filter.add_rule('type', format_type, type_choices)

        # color filter
        color_code = {
            'red': 1,
            'orange': 256,
            'yellow': 2,
            'green': 4,
            'purple': 32,
            'pink': 64,
            'teal': 8,
            'blue': 16,
            'brown': 12,
            'white': 1024,
            'black': 512,
            'blackandwhite': 2048
        }

        def format_color(color):
            return 'ic={}'.format(color_code[color])

        color_choices = list(color_code.keys())
        search_filter.add_rule('color', format_color, color_choices)

        # size filter
        def format_size(size):
            if size in ['extralarge', 'large', 'medium', 'small']:
                size_code = {
                    'extralarge': 9,
                    'large': 3,
                    'medium': 2,
                    'small': 1
                }
                return 'z={}'.format(size_code[size])
            elif size.startswith('='):
                wh = size[1:].split('x')
                assert len(wh) == 2
                return 'width={}&height={}'.format(*wh)
            else:
                raise ValueError(
                    'filter option "size" must be one of the following: '
                    'extralarge, large, medium, small, >[]x[] '
                    '([] is an integer)')

        search_filter.add_rule('size', format_size)

        return search_filter

    def feed(self, keyword, offset, max_num, filters=None):
        base_url = ('http://image.baidu.com/search/acjson?tn=resultjson_com'
                    '&ipn=rj&word={}&pn={}&rn=30')
        self.filter = self.get_filter()
        filter_str = self.filter.apply(filters, sep='&')
        for i in range(offset, offset + max_num, 30):
            url = base_url.format(keyword, i)
            if filter_str:
                url += '&' + filter_str
            self.out_queue.put(url)
            self.logger.debug('put url to url_queue: {}'.format(url))


class BaiduParser(Parser):

    def _decode_url(self, encrypted_url):
        url = encrypted_url
        map1 = {'_z2C$q': ':', '_z&e3B': '.', 'AzdH3F': '/'}
        map2 = {
            'w': 'a', 'k': 'b', 'v': 'c', '1': 'd', 'j': 'e',
            'u': 'f', '2': 'g', 'i': 'h', 't': 'i', '3': 'j',
            'h': 'k', 's': 'l', '4': 'm', 'g': 'n', '5': 'o',
            'r': 'p', 'q': 'q', '6': 'r', 'f': 's', 'p': 't',
            '7': 'u', 'e': 'v', 'o': 'w', '8': '1', 'd': '2',
            'n': '3', '9': '4', 'c': '5', 'm': '6', '0': '7',
            'b': '8', 'l': '9', 'a': '0'
        }  # yapf: disable
        for (ciphertext, plaintext) in map1.items():
            url = url.replace(ciphertext, plaintext)
        char_list = [char for char in url]
        for i in range(len(char_list)):
            if char_list[i] in map2:
                char_list[i] = map2[char_list[i]]
        url = ''.join(char_list)
        return url

    def parse(self, response):
        try:
            content = response.content.decode('utf-8', 'ignore')
            content = json.loads(content, strict=False)
        except:
            self.logger.error('Fail to parse the response in json format')
            return
        for item in content['data']:
            if 'objURL' in item:
                img_url = self._decode_url(item['objURL'])
            elif 'hoverURL' in item:
                img_url = item['hoverURL']
            else:
                continue
            yield dict(file_url=img_url)


class BaiduImageCrawler(Crawler):

    def __init__(self,
                 feeder_cls=BaiduFeeder,
                 parser_cls=BaiduParser,
                 downloader_cls=ImageDownloader,
                 *args,
                 **kwargs):
        super(BaiduImageCrawler, self).__init__(
            feeder_cls, parser_cls, downloader_cls, *args, **kwargs)

    def crawl(self,
              keyword,
              filters=None,
              offset=0,
              max_num=1000,
              min_size=None,
              max_size=None,
              file_idx_offset=0,
              overwrite=False):
        if offset + max_num > 1000:
            if offset > 1000:
                self.logger.error('Offset cannot exceed 1000, otherwise you '
                                  'will get duplicated searching results.')
                return
            elif max_num > 1000:
                max_num = 1000 - offset
                self.logger.warning('Due to Baidu\'s limitation, you can only '
                                    'get the first 1000 result. "max_num" has '
                                    'been automatically set to %d',
                                    1000 - offset)
        else:
            pass
        feeder_kwargs = dict(
            keyword=keyword, offset=offset, max_num=max_num, filters=filters)
        downloader_kwargs = dict(
            max_num=max_num,
            min_size=min_size,
            max_size=max_size,
            file_idx_offset=file_idx_offset,
            overwrite=overwrite)
        super(BaiduImageCrawler, self).crawl(
            feeder_kwargs=feeder_kwargs, downloader_kwargs=downloader_kwargs)
