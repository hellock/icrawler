# -*- coding: utf-8 -*-

import json

from icrawler import Crawler, Parser, SimpleSEFeeder, ImageDownloader


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
        content = json.loads(response.content.decode('utf-8'))
        for item in content['data']:
            if 'objURL' in item:
                img_url = self._decode_url(item['objURL'])
            elif 'hoverURL' in item:
                img_url = item['hoverURL']
            else:
                continue
            yield dict(file_url=img_url)


class BaiduImageCrawler(Crawler):

    def __init__(self, *args, **kwargs):
        super(BaiduImageCrawler, self).__init__(
            feeder_cls=SimpleSEFeeder,
            parser_cls=BaiduParser,
            downloader_cls=ImageDownloader,
            *args,
            **kwargs)

    def crawl(self,
              keyword,
              offset=0,
              max_num=1000,
              min_size=None,
              max_size=None,
              file_idx_offset=0):
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
            url_template=('http://image.baidu.com/search/acjson?'
                          'tn=resultjson_com&ipn=rj&word={}&pn={}&rn=30'),
            keyword=keyword,
            offset=offset,
            max_num=max_num,
            page_step=30)
        downloader_kwargs = dict(
            max_num=max_num,
            min_size=min_size,
            max_size=max_size,
            file_idx_offset=file_idx_offset)
        super(BaiduImageCrawler, self).crawl(
            feeder_kwargs=feeder_kwargs, downloader_kwargs=downloader_kwargs)
