# -*- coding: utf-8 -*-

import logging
import re

from bs4 import BeautifulSoup
from six.moves import html_parser

from icrawler import Crawler, Parser, SimpleSEFeeder, ImageDownloader


class BingParser(Parser):

    def parse(self, response):
        soup = BeautifulSoup(response.content, 'lxml')
        image_divs = soup.find_all('div', class_='dg_u')
        pattern = re.compile(r'imgurl:\"(.*?)\.jpg')
        for div in image_divs:
            href_str = html_parser.HTMLParser().unescape(div.a['m'])
            match = pattern.search(href_str)
            if match:
                img_url = '{}.jpg'.format(match.group(1))
                yield dict(file_url=img_url)


class BingImageCrawler(Crawler):

    def __init__(self, *args, **kwargs):
        super(BingImageCrawler, self).__init__(
            feeder_cls=SimpleSEFeeder,
            parser_cls=BingParser,
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
