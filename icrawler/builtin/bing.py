# -*- coding: utf-8 -*-

import re

import six
from bs4 import BeautifulSoup
from six.moves import html_parser

from icrawler import Crawler, Parser, Feeder, ImageDownloader
from icrawler.builtin.filter import Filter


class BingFeeder(Feeder):

    def get_filter(self):
        search_filter = Filter()

        # type filter
        def format_type(img_type):
            prefix = '+filterui:photo-'
            return (prefix + 'animatedgif'
                    if img_type == 'animated' else prefix + img_type)

        type_choices = [
            'photo', 'clipart', 'linedrawing', 'transparent', 'animated'
        ]
        search_filter.add_rule('type', format_type, type_choices)

        # color filter
        def format_color(color):
            prefix = '+filterui:color2-'
            if color == 'color':
                return prefix + 'color'
            elif color == 'blackandwhite':
                return prefix + 'bw'
            else:
                return prefix + 'FGcls_' + color.upper()

        color_choices = [
            'color', 'blackandwhite', 'red', 'orange', 'yellow', 'green',
            'teal', 'blue', 'purple', 'pink', 'white', 'gray', 'black', 'brown'
        ]
        search_filter.add_rule('color', format_color, color_choices)

        # size filter
        def format_size(size):
            if size in ['large', 'medium', 'small']:
                return '+filterui:imagesize-' + size
            elif size == 'extralarge':
                return '+filterui:imagesize-wallpaper'
            elif size.startswith('>'):
                wh = size[1:].split('x')
                assert len(wh) == 2
                return '+filterui:imagesize-custom_{}_{}'.format(*wh)
            else:
                raise ValueError(
                    'filter option "size" must be one of the following: '
                    'extralarge, large, medium, small, >[]x[] '
                    '([] is an integer)')

        search_filter.add_rule('size', format_size)

        # licence filter
        license_code = {
            'creativecommons': 'licenseType-Any',
            'publicdomain': 'license-L1',
            'noncommercial': 'license-L2_L3_L4_L5_L6_L7',
            'commercial': 'license-L2_L3_L4',
            'noncommercial,modify': 'license-L2_L3_L5_L6',
            'commercial,modify': 'license-L2_L3'
        }

        def format_license(license):
            return '+filterui:' + license_code[license]

        license_choices = list(license_code.keys())
        search_filter.add_rule('license', format_license, license_choices)

        # layout filter
        layout_choices = ['square', 'wide', 'tall']
        search_filter.add_rule('layout', lambda x: '+filterui:aspect-' + x,
                               layout_choices)

        # people filter
        people_choices = ['face', 'portrait']
        search_filter.add_rule('people', lambda x: '+filterui:face-' + x,
                               people_choices)

        # date filter
        date_minutes = {
            'pastday': 1440,
            'pastweek': 10080,
            'pastmonth': 43200,
            'pastyear': 525600
        }

        def format_date(date):
            return '+filterui:age-lt' + str(date_minutes[date])

        date_choices = list(date_minutes.keys())
        search_filter.add_rule('date', format_date, date_choices)

        return search_filter

    def feed(self, keyword, offset, max_num, filters=None):
        base_url = 'https://www.bing.com/images/async?q={}&first={}'
        self.filter = self.get_filter()
        filter_str = self.filter.apply(filters)
        filter_str = '&qft=' + filter_str if filter_str else ''

        for i in range(offset, offset + max_num, 20):
            url = base_url.format(keyword, i) + filter_str
            self.out_queue.put(url)
            self.logger.debug('put url to url_queue: {}'.format(url))


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
                 feeder_cls=BingFeeder,
                 parser_cls=BingParser,
                 downloader_cls=ImageDownloader,
                 *args,
                 **kwargs):
        super(BingImageCrawler, self).__init__(feeder_cls, parser_cls,
                                               downloader_cls, *args, **kwargs)

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
                self.logger.warning('Due to Bing\'s limitation, you can only '
                                    'get the first 1000 result. "max_num" has '
                                    'been automatically set to %d',
                                    1000 - offset)
        feeder_kwargs = dict(
            keyword=keyword, offset=offset, max_num=max_num, filters=filters)
        downloader_kwargs = dict(
            max_num=max_num,
            min_size=min_size,
            max_size=max_size,
            file_idx_offset=file_idx_offset,
            overwrite=overwrite)
        super(BingImageCrawler, self).crawl(
            feeder_kwargs=feeder_kwargs, downloader_kwargs=downloader_kwargs)
