# -*- coding: utf-8 -*-

import re
import time

from bs4 import BeautifulSoup
from six.moves.urllib.parse import urljoin, urlsplit

from icrawler import Crawler, Feeder, Parser, ImageDownloader


class GreedyFeeder(Feeder):

    def feed(self, domains):
        for domain in domains:
            self.output(domain)
        while not self.signal.get('reach_max_num'):
            time.sleep(1)


class GreedyParser(Parser):

    def __init__(self, *args, **kwargs):
        self.pattern = re.compile(
            r'(http|\/\/)(.*)\.(jpg|jpeg|png|bmp|gif|tiff)')
        super(GreedyParser, self).__init__(*args, **kwargs)

    def is_in_domain(self, url, domains):
        for domain in domains:
            if domain in url:
                return True
        return False

    def parse(self, response, domains):
        soup = BeautifulSoup(
            response.content.decode('utf-8', 'ignore'), 'lxml')
        tags = soup.find_all('img', src=True)
        for tag in tags:
            if re.match(self.pattern, tag['src']):
                if tag['src'].startswith('//'):
                    img_url = 'http:' + tag['src']
                else:
                    img_url = tag['src']
                yield dict(file_url=img_url)
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
                yield dict(file_url=href)
            else:
                # discard urls such as 'www.example.com/file.zip'
                # TODO: deal with '#' in the urls
                tmp = href.split('/')[-1].split('.')
                if len(tmp) > 1 and tmp[-1] not in [
                        'html', 'shtml', 'shtm', 'php', 'jsp', 'asp'
                ]:
                    continue
                # discard urls such as 'javascript:void(0)'
                elif href.find('javascript', 0, 10) == 0:
                    continue
                # discard urls such as 'android-app://xxxxxxxxx'
                elif urlsplit(href).scheme not in ['http', 'https', 'ftp']:
                    continue
                # urls of the same domain
                elif self.is_in_domain(href, domains):
                    yield href


class GreedyImageCrawler(Crawler):

    def __init__(self,
                 feeder_cls=GreedyFeeder,
                 parser_cls=GreedyParser,
                 downloader_cls=ImageDownloader,
                 *args,
                 **kwargs):
        super(GreedyImageCrawler, self).__init__(
            feeder_cls, parser_cls, downloader_cls, *args, **kwargs)

    def crawl(self,
              domains,
              max_num=0,
              min_size=None,
              max_size=None,
              file_idx_offset=0):
        if isinstance(domains, str):
            domains = [domains]
        elif not isinstance(domains, list):
            self.logger.error('domains must be a string or a list')
        for i in range(len(domains)):
            if not domains[i].startswith('http'):
                domains[i] = 'http://' + domains[i]
            domains[i] = domains[i].rstrip('/')
        super(GreedyImageCrawler, self).crawl(
            feeder_kwargs={'domains': domains},
            parser_kwargs={'domains': domains},
            downloader_kwargs=dict(
                max_num=max_num,
                min_size=min_size,
                max_size=max_size,
                file_idx_offset=file_idx_offset))
