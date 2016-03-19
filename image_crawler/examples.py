# -*- coding: utf-8 -*-

from bs4 import BeautifulSoup
import html
from image_crawler.crawler import ImageCrawler
import json
import logging
import re
# from image_crawler.downloader import Downloader
from image_crawler.feeder import SimpleSEFeeder
from image_crawler.parser import Parser


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
        ImageCrawler.__init__(self, img_dir, feeder_cls=SimpleSEFeeder,
                              parser_cls=GoogleParser, log_level=log_level)

    def crawl(self, keyword, max_num, feeder_num=1, parser_num=1,
              downloader_num=1, offset=0):
        feeder_kwargs = dict(
            url_template='https://www.google.com/search?q={}&tbm=isch&start={}',
            keyword=keyword,
            offset=offset,
            max_num=max_num,
            page_step=100
        )
        downloader_kwargs = dict(max_num=max_num)
        super(GoogleImageCrawler, self).crawl(feeder_num, parser_num, downloader_num,
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

    def __init__(self, img_dir='images', parser_cls=BingParser):
        ImageCrawler.__init__(self, img_dir, parser_cls)

    def prepare(self, max_num, keyword):
        self.max_num = max_num
        self.start_urls = []
        for i in range(0, self.max_num, 35):
            self.start_urls.append(
                'http://www.bing.com/images/search?q={}&count'
                '=35&first={}'.format(keyword, i)
            )


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

    def __init__(self, img_dir='images', parser_cls=BaiduParser):
        ImageCrawler.__init__(self, img_dir, parser_cls)

    def prepare(self, max_num, keyword):
        self.max_num = max_num
        self.start_urls = []
        for i in range(0, self.max_num, 30):
            self.start_urls.append(
                'http://image.baidu.com/search/acjson?tn=resultjson_com'
                '&ipn=rj&word={}&pn={}&rn=30'.format(keyword, i + 30)
            )
