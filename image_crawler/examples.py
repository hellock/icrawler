# -*- coding: utf-8 -*-

import html
import json
import logging
import re
from bs4 import BeautifulSoup
from image_crawler.crawler import ImageCrawler
from image_crawler.feeder import Feeder
from image_crawler.feeder import SimpleSEFeeder
from image_crawler.parser import Parser


class GoogleFeeder(Feeder):

    def feed(self, keyword, offset, max_num):
        for i in range(offset, offset + max_num, 100):
            url = 'https://www.google.com/search?q={}&tbm=isch&ijn={}&start={}'.format(keyword, int(i/100), i)
            self.url_queue.put(url)
            self.logger.debug('put url to url_queue: {}'.format(url))


class GoogleParser(Parser):

    def parse(self, response):
        soup = BeautifulSoup(response, 'lxml')
        image_divs = soup.find_all('div', class_='rg_di rg_el ivg-i')
        pattern = re.compile(r'imgurl=(.*?)\.jpg')
        for div in image_divs:
            href_str = div.a['href']
            match = pattern.search(href_str)
            if match:
                img_url = '{}.jpg'.format(match.group(1))
                self.task_queue.put(dict(img_url=img_url))


class GoogleImageCrawler(ImageCrawler):

    def __init__(self, img_dir='images', log_level=logging.INFO):
        ImageCrawler.__init__(self, img_dir, feeder_cls=GoogleFeeder,
                              parser_cls=GoogleParser, log_level=log_level)

    def crawl(self, keyword, max_num, feeder_thr_num=1, parser_thr_num=1,
              downloader_thr_num=1, offset=0):
        if offset + max_num > 1000:
            if offset > 1000:
                self.logger.error('Offset cannot exceed 1000, otherwise you '
                                  'will get duplicated searching results.')
                return
            elif max_num > 1000:
                max_num = 1000 - offset
                self.logger.warning('Due to Google\'s limitation, you can only '
                                    'get the first 1000 result. "max_num" has '
                                    'been automatically set to %d', 1000-offset)
        else:
            pass
        feeder_kwargs = dict(
            keyword=keyword,
            offset=offset,
            max_num=max_num,
        )
        downloader_kwargs = dict(max_num=max_num)
        super(GoogleImageCrawler, self).crawl(
            feeder_thr_num, parser_thr_num, downloader_thr_num,
            feeder_kwargs=feeder_kwargs,
            downloader_kwargs=downloader_kwargs)


class BingParser(Parser):

    def parse(self, response):
        soup = BeautifulSoup(response, 'lxml')
        image_divs = soup.find_all('div', class_='dg_u')
        pattern = re.compile(r'imgurl:\"(.*?)\.jpg')
        for div in image_divs:
            href_str = html.unescape(div.a['m'])
            match = pattern.search(href_str)
            if match:
                img_url = '{}.jpg'.format(match.group(1))
                self.task_queue.put(dict(img_url=img_url))


class BingImageCrawler(ImageCrawler):

    def __init__(self, img_dir='images', log_level=logging.INFO):
        ImageCrawler.__init__(self, img_dir, feeder_cls=SimpleSEFeeder,
                              parser_cls=BingParser, log_level=log_level)

    def crawl(self, keyword, max_num, feeder_thr_num=1, parser_thr_num=1,
              downloader_thr_num=1, offset=0):
        if offset + max_num > 1000:
            if offset > 1000:
                self.logger.error('Offset cannot exceed 1000, otherwise you '
                                  'will get duplicated searching results.')
                return
            elif max_num > 1000:
                max_num = 1000 - offset
                self.logger.warning('Due to Bing\'s limitation, you can only '
                                    'get the first 1000 result. "max_num" has '
                                    'been automatically set to %d', 1000-offset)
        else:
            pass
        feeder_kwargs = dict(
            url_template='http://www.bing.com/images/search?q={}&count=35&first={}',
            keyword=keyword,
            offset=offset,
            max_num=max_num,
            page_step=35
        )
        downloader_kwargs = dict(max_num=max_num)
        super(BingImageCrawler, self).crawl(
            feeder_thr_num, parser_thr_num, downloader_thr_num,
            feeder_kwargs=feeder_kwargs,
            downloader_kwargs=downloader_kwargs)


class BaiduParser(Parser):

    def _decode_url(self, encrypted_url):
        url = encrypted_url
        map1 = {'_z2C$q': ':', '_z&e3B': '.', 'AzdH3F': '/'}
        map2 = {'w': 'a', 'k': 'b', 'v': 'c', '1': 'd', 'j': 'e',
                'u': 'f', '2': 'g', 'i': 'h', 't': 'i', '3': 'j',
                'h': 'k', 's': 'l', '4': 'm', 'g': 'n', '5': 'o',
                'r': 'p', 'q': 'q', '6': 'r', 'f': 's', 'p': 't',
                '7': 'u', 'e': 'v', 'o': 'w', '8': '1', 'd': '2',
                'n': '3', '9': '4', 'c': '5', 'm': '6', '0': '7',
                'b': '8', 'l': '9', 'a': '0'}
        for (ciphertext, plaintext) in map1.items():
            url = url.replace(ciphertext, plaintext)
        char_list = [char for char in url]
        for i in range(len(char_list)):
            if char_list[i] in map2:
                char_list[i] = map2[char_list[i]]
        url = ''.join(char_list)
        return url

    def parse(self, response):
        content = json.loads(response.decode())
        for item in content['data']:
            if 'objURL' in item:
                img_url = self._decode_url(item['objURL'])
            elif 'hoverURL' in item:
                img_url = item['hoverURL']
            else:
                continue
            self.task_queue.put(dict(img_url=img_url))


class BaiduImageCrawler(ImageCrawler):

    def __init__(self, img_dir='images', log_level=logging.INFO):
        ImageCrawler.__init__(self, img_dir, feeder_cls=SimpleSEFeeder,
                              parser_cls=BaiduParser, log_level=log_level)

    def crawl(self, keyword, max_num, feeder_thr_num=1, parser_thr_num=1,
              downloader_thr_num=1, offset=0):
        if offset + max_num > 1000:
            if offset > 1000:
                self.logger.error('Offset cannot exceed 1000, otherwise you '
                                  'will get duplicated searching results.')
                return
            elif max_num > 1000:
                max_num = 1000 - offset
                self.logger.warning('Due to Baidu\'s limitation, you can only '
                                    'get the first 1000 result. "max_num" has '
                                    'been automatically set to %d', 1000-offset)
        else:
            pass
        feeder_kwargs = dict(
            url_template='http://image.baidu.com/search/acjson?'
                         'tn=resultjson_com&ipn=rj&word={}&pn={}&rn=30',
            keyword=keyword,
            offset=offset+30,
            max_num=max_num,
            page_step=30
        )
        downloader_kwargs = dict(max_num=max_num)
        super(BaiduImageCrawler, self).crawl(
            feeder_thr_num, parser_thr_num, downloader_thr_num,
            feeder_kwargs=feeder_kwargs,
            downloader_kwargs=downloader_kwargs)
