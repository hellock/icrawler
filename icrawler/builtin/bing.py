# -*- coding: utf-8 -*-

import re

import six
from bs4 import BeautifulSoup
from six.moves import html_parser

from icrawler import Crawler, Parser, SimpleSEFeeder, ImageDownloader


class BingParser(Parser):

    def parse(self, response):
        soup = BeautifulSoup(
            response.content.decode('utf-8', 'ignore'), 'lxml')
        image_divs = soup.find_all('div', class_='imgpt')
        pattern = re.compile(r'murl\":\"(.*?)\.jpg')
        for div in image_divs:
            href_str = html_parser.HTMLParser().unescape(div.a['m'])
            match = pattern.search(href_str)
            if match:
                name = (match.group(1)
                        if six.PY3 else match.group(1).encode('utf-8'))
                img_url = '{}.jpg'.format(name)
                yield dict(file_url=img_url)


class BingImageCrawler(Crawler):

    def __init__(self,
                 feeder_cls=SimpleSEFeeder,
                 parser_cls=BingParser,
                 downloader_cls=ImageDownloader,
                 *args,
                 **kwargs):
        super(BingImageCrawler, self).__init__(feeder_cls, parser_cls,
                                               downloader_cls, *args, **kwargs)

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
                self.logger.warning('Due to Bing\'s limitation, you can only '
                                    'get the first 1000 result. "max_num" has '
                                    'been automatically set to %d',
                                    1000 - offset)
        feeder_kwargs = dict(
            url_template=('http://www.bing.com/images/search?'
                          'q={}&count=35&first={}'),
            keyword=keyword,
            offset=offset,
            max_num=max_num,
            page_step=35)
        downloader_kwargs = dict(
            max_num=max_num,
            min_size=min_size,
            max_size=max_size,
            file_idx_offset=file_idx_offset)
        super(BingImageCrawler, self).crawl(
            feeder_kwargs=feeder_kwargs, downloader_kwargs=downloader_kwargs)
