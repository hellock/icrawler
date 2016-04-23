# -*- coding: utf-8 -*-

import logging
import re
from bs4 import BeautifulSoup
from six.moves.urllib.parse import urlsplit
from six.moves.urllib.parse import urljoin

from .. import Feeder
from .. import Parser
from .. import Crawler


class GreedyFeeder(Feeder):

    def feed(self, domains):
        if isinstance(domains, str):
            self.domains = [domains]
        elif isinstance(domains, list):
            self.domains = domains
        else:
            self.error('domains must be a string or a list')
        for domain in self.domains:
            self.put_url_into_queue('http://' +
                                    urlsplit(domain).geturl().rstrip('/'))
        while not self.global_signal.get('reach_max_num'):
            pass


class GreedyParser(Parser):

    def __init__(self, url_queue, task_queue, signal, session):
        self.pattern = re.compile(r'http(.*)\.(jpg|jpeg|png|bmp|gif|tiff|ico)')
        super(GreedyParser, self).__init__(url_queue, task_queue, signal,
                                           session)

    def is_in_domain(self, url, domains):
        for domain in domains:
            if domain in url:
                return True
        return False

    def parse(self, response, feeder):
        soup = BeautifulSoup(response.content, 'lxml')
        tags = soup.find_all('img', src=True)
        for tag in tags:
            if re.match(self.pattern, tag['src']):
                self.put_task_into_queue(dict(img_url=tag['src']))
        tags = soup.find_all(href=True)
        base_url = '{0.scheme}://{0.netloc}'.format(urlsplit(response.url))
        for tag in tags:
            href = tag['href']
            # deal with urls start with '//' or '/' or '#'
            if len(href) < 2:
                continue
            if href[0:2] == '//':
                href = 'http:' + href.rstrip('/')
            elif href[0] == '/':
                href = urljoin(base_url, href.strip('/'))
            elif href[0] == '#':
                continue
            else:
                href = urljoin(base_url, href.rstrip('/'))
            # if it is a image url
            if re.match(self.pattern, href):
                self.put_task_into_queue(dict(img_url=href))
            else:
                # discard urls such as 'www.example.com/file.zip'
                # TODO: deal with '#' in the urls
                tmp = href.split('/')[-1].split('.')
                if len(tmp) > 1 and tmp[-1] not in [
                        'html', 'html', 'shtml', 'shtm', 'php', 'jsp', 'asp']:
                    continue
                # discard urls such as 'javascript:void(0)'
                elif href.find('javascript', 0, 10) == 0:
                    continue
                # discard urls such as 'android-app://xxxxxxxxx'
                elif urlsplit(href).scheme not in ['http', 'https', 'ftp']:
                    continue
                # urls of the same domain
                elif self.is_in_domain(href, feeder.domains):
                    feeder.put_url_into_queue(href)


class GreedyImageCrawler(Crawler):

    def __init__(self, img_dir='images', log_level=logging.INFO):
        super(GreedyImageCrawler, self).__init__(
            img_dir, feeder_cls=GreedyFeeder,
            parser_cls=GreedyParser, log_level=log_level)

    def crawl(self, domains, max_num=0, parser_thr_num=1, downloader_thr_num=1,
              min_size=None, max_size=None):
        super(GreedyImageCrawler, self).crawl(
            1, parser_thr_num, downloader_thr_num,
            feeder_kwargs={'domains': domains},
            parser_kwargs={'feeder': self.feeder},
            downloader_kwargs=dict(max_num=max_num, min_size=min_size,
                                   max_size=max_size))
