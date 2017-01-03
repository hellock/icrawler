# -*- coding: utf-8 -*-

import json

from bs4 import BeautifulSoup
from six.moves.urllib.parse import urlencode

from icrawler import Crawler, Feeder, Parser, ImageDownloader


class GoogleFeeder(Feeder):

    def feed(self, keyword, offset, max_num, date_min, date_max):
        base_url = 'https://www.google.com/search?'
        for i in range(offset, offset + max_num, 100):
            cd_min = date_min.strftime('%d/%m/%Y') if date_min else ''
            cd_max = date_max.strftime('%d/%m/%Y') if date_max else ''
            tbs = 'cdr:1,cd_min:{},cd_max:{}'.format(cd_min, cd_max)
            params = dict(
                q=keyword, ijn=int(i / 100), start=i, tbs=tbs, tbm='isch')
            url = base_url + urlencode(params)
            self.out_queue.put(url)
            self.logger.debug('put url to url_queue: {}'.format(url))


class GoogleParser(Parser):

    def parse(self, response):
        soup = BeautifulSoup(response.content, 'lxml')
        image_divs = soup.find_all('div', class_='rg_meta')
        for div in image_divs:
            meta = json.loads(div.text)
            if 'ou' in meta:
                yield dict(file_url=meta['ou'])


class GoogleImageCrawler(Crawler):

    def __init__(self, *args, **kwargs):
        super(GoogleImageCrawler, self).__init__(
            feeder_cls=GoogleFeeder,
            parser_cls=GoogleParser,
            downloader_cls=ImageDownloader,
            *args,
            **kwargs)

    def crawl(self,
              keyword,
              offset=0,
              max_num=1000,
              date_min=None,
              date_max=None,
              min_size=None,
              max_size=None,
              file_idx_offset=0):
        if offset + max_num > 1000:
            if offset > 1000:
                self.logger.error(
                    '"Offset" cannot exceed 1000, otherwise you will get '
                    'duplicated searching results.')
                return
            elif max_num > 1000:
                max_num = 1000 - offset
                self.logger.warning(
                    'Due to Google\'s limitation, you can only get the first '
                    '1000 result. "max_num" has been automatically set to %d. '
                    'If you really want to get more than 1000 results, you '
                    'can specify different date ranges.', 1000 - offset)

        feeder_kwargs = dict(
            keyword=keyword,
            offset=offset,
            max_num=max_num,
            date_min=date_min,
            date_max=date_max)
        downloader_kwargs = dict(
            max_num=max_num,
            min_size=min_size,
            max_size=max_size,
            file_idx_offset=file_idx_offset)
        super(GoogleImageCrawler, self).crawl(
            feeder_kwargs=feeder_kwargs, downloader_kwargs=downloader_kwargs)
