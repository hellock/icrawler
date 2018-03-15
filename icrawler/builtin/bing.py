# -*- coding: utf-8 -*-

import re

import six
from bs4 import BeautifulSoup
from six.moves import html_parser

from icrawler import Crawler, Parser, Feeder, ImageDownloader


class BingFeeder(Feeder):

    def feed(self,
             keyword,
             offset,
             max_num,
             img_type=None,
             img_layout=None,
             img_people=None,
             img_color=None,
             img_license=None,
             img_age=None):
        base_url = 'https://www.bing.com/images/search?scope=images&q={}&first={}&qft='
        
        if img_license and img_license not in ['licenseType-Any', 'license-L2_L3_L4_L5_L6_L7', 'license-L2_L3_L4', 
                                       'license-L2_L3_L5_L6', 'license-L1',
                                       'license-L2_L3']:
            # All Creative Commons - licenseType-Any
            # Public domain - license-L1
            # Free to share and use - license-L2_L3_L4_L5_L6_L7
            # Free to share and use commercially - license-L2_L3_L4
            # Free to modify, share, and use - license-L2_L3_L5_L6
            # Free to modify, share, and use commercially - license-L2_L3
            raise ValueError(
                ''' "img_license" must be one of the following: licenseType-Any, license-L2_L3_L4_L5_L6_L7, 
                license-L2_L3_L4, license-L2_L3_L5_L6, license-L2_L3, 'license-L1' ''')
        
        if img_type and img_type not in [
                'photo', 'clipart', 'transparent', 'animatedgif']:
            # photo - photograph
            # clipart: clip art
            # animatedgif - gif
            # transparent - 
            raise ValueError('"img_type" must be one of the following: '
                             'photo, clipart, transparent, animatedgif')
        
        if img_color and img_color not in [
                'color', 'bw', 'red', 'orange',
                'yellow', 'green', 'teal', 'blue', 'purple', 'pink', 'white',
                'gray', 'black', 'brown']:
            # color: full color
            # blackandwhite: black and white
            # transparent: transparent
            # red, orange, yellow, green, teal, blue, purple, pink, white, gray, black, brown
            raise ValueError(
                '"img_color" must be one of the following: '
                'color, bw, red, orange, yellow, '
                'green, teal, blue, purple, pink, white, gray, black, brown')
        # Fix codes for image color
        colorprefix = 'color2-'
        if img_color and img_color in [ 'color', 'bw']:
            img_color = color_prefix + img_color
        elif img_color:
            img_color = color_prefix + 'FGcls_' + img_color.upper()
            
            
        if img_layout and img_layout not in ['square', 'wide', 'tall']:
            # square : square
            # wide : width more than height
            # tall : height more than width
            raise ValueError('"img_layout" must be one of the following: square, wide, tall')
        # Fix layout prefix
        layout_prefix = 'layout-'    
        if img_layout:
            img_layout = layout_prefix + img_layout

        if img_people and img_people not in ['face', 'portrait']:
            # face - Just face
            # portrait - face and shoulders
            raise ValueError('"img_layout" must be one of: face, portrait')
        # Fix people prefix
        people_prefix = 'face-'
        if img_people:
            img_people = people_prefix + img_people

        if img_age and img_age.isdigit():
            # Number of minutes in the past from the current moment that you want to look at
            raise ValueError('"img_age" should be a number')
        # fix age prefix
        age_prefix = 'age-tl'
        if img_age:
            img_age = age_prefix + img_age 

        for i in range(offset, offset + max_num, 20):
            img_license = '' if img_license is None else img_license
            img_type = '' if img_type is None else img_type
            img_color = '' if img_color is None else img_color
            img_people = '' if img_people is None else img_people
            img_layout = '' if img_layout is None else img_layout
            img_age = '' if img_age is None else img_age
            url = base_url.format(keyword, i)
            for property in [img_license, img_type, img_color, img_people, img_layout, img_age]:
                if property:
                    url = url + '+filterui:' + property
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
              offset=0,
              max_num=1000,
              min_size=None,
              max_size=None,
              img_type=None,
              img_layout=None,
              img_people=None,
              img_color=None,
              img_license=None,
              img_age=None,
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
            keyword=keyword,
            offset=offset,
            max_num=max_num,
            img_type=img_type,
            img_layout=img_layout,
            img_people=img_people,
            img_color=img_color,
            img_license=img_license,
            img_age=img_age)
        downloader_kwargs = dict(
            max_num=max_num,
            min_size=min_size,
            max_size=max_size,
            file_idx_offset=file_idx_offset)
        super(BingImageCrawler, self).crawl(
            feeder_kwargs=feeder_kwargs, downloader_kwargs=downloader_kwargs)
