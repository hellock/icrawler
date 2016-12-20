# -*- coding: utf-8 -*-

import logging
import re

from bs4 import BeautifulSoup
from six.moves import html_parser

from icrawler import Crawler, Parser, SimpleSEFeeder


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
                self.put_task_into_queue(dict(img_url=img_url))


class BingImageCrawler(Crawler):

    def __init__(self, img_dir='images', log_level=logging.INFO):
        super(BingImageCrawler, self).__init__(
            img_dir, feeder_cls=SimpleSEFeeder,
            parser_cls=BingParser, log_level=log_level)

    def crawl(self, keyword, offset=0, max_num=1000, feeder_thr_num=1,
              parser_thr_num=1, downloader_thr_num=1,
              min_size=None, max_size=None, save_mode='overwrite'):
        if offset + max_num > 1000:
            if offset > 1000:
                self.logger.error('Offset cannot exceed 1000, otherwise you '
                                  'will get duplicated searching results.')
                return
            elif max_num > 1000:
                max_num = 1000 - offset
                self.logger.warning('Due to Bing\'s limitation, you can only '
                                    'get the first 1000 result. "max_num" has '
                                    'been automatically set to %d', 1000 - offset)
        else:
            pass
        feeder_kwargs = dict(
            url_template='http://www.bing.com/images/search?q={}&count=35&first={}',
            keyword=keyword,
            offset=offset,
            max_num=max_num,
            page_step=35
        )
        downloader_kwargs = dict(max_num=max_num, min_size=min_size,
                                 max_size=max_size, save_mode=save_mode)
        super(BingImageCrawler, self).crawl(
            feeder_thr_num, parser_thr_num, downloader_thr_num,
            feeder_kwargs=feeder_kwargs,
            downloader_kwargs=downloader_kwargs)
