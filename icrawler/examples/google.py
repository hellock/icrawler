# -*- coding: utf-8 -*-

import json
import logging
from bs4 import BeautifulSoup
from six.moves.urllib.parse import urlencode

from .. import Feeder
from .. import Parser
from .. import Crawler


class GoogleFeeder(Feeder):

    def feed(self, keyword, offset, max_num, date_min, date_max):
        base_url = 'https://www.google.com/search?'
        for i in range(offset, offset + max_num, 100):
            if date_min is not None:
                dmin = date_min.strftime('%d/%m/%Y')
            else:
                dmin = ''
            if date_max is not None:
                dmax = date_max.strftime('%d/%m/%Y')
            else:
                dmax = ''
            tbs = 'cdr:1,cd_min:{},cd_max:{}'.format(dmin, dmax)
            params = dict(q=keyword, ijn=int(i / 100), start=i, tbs=tbs,
                          tbm='isch')
            url = base_url + urlencode(params)
            self.put_url_into_queue(url)
            self.logger.debug('put url to url_queue: {}'.format(url))


class GoogleParser(Parser):

    def parse(self, response):
        soup = BeautifulSoup(response.content, 'lxml')
        image_divs = soup.find_all('div', class_='rg_meta')
        for div in image_divs:
            meta = json.loads(div.text)
            if 'ou' in meta:
                self.put_task_into_queue(dict(img_url=meta['ou']))


class GoogleImageCrawler(Crawler):

    def __init__(self, img_dir='images', log_level=logging.INFO):
        super(GoogleImageCrawler, self).__init__(
            img_dir, feeder_cls=GoogleFeeder,
            parser_cls=GoogleParser, log_level=log_level)

    def crawl(self, keyword, offset=0, max_num=1000, date_min=None,
              date_max=None, feeder_thr_num=1, parser_thr_num=1,
              downloader_thr_num=1, min_size=None, max_size=None):
        if offset + max_num > 1000:
            if offset > 1000:
                self.logger.error('Offset cannot exceed 1000, otherwise you '
                                  'will get duplicated searching results.')
                return
            elif max_num > 1000:
                max_num = 1000 - offset
                self.logger.warning('Due to Google\'s limitation, you can only '
                                    'get the first 1000 result. "max_num" has '
                                    'been automatically set to %d',
                                    1000 - offset)
        else:
            pass
        feeder_kwargs = dict(
            keyword=keyword,
            offset=offset,
            max_num=max_num,
            date_min=date_min,
            date_max=date_max
        )
        downloader_kwargs = dict(max_num=max_num, min_size=min_size,
                                 max_size=max_size)
        super(GoogleImageCrawler, self).crawl(
            feeder_thr_num, parser_thr_num, downloader_thr_num,
            feeder_kwargs=feeder_kwargs,
            downloader_kwargs=downloader_kwargs)
