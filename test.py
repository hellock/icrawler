# -*- coding: utf-8 -*-

import logging
import sys
from datetime import date

from icrawler.builtin import (BaiduImageCrawler, BingImageCrawler,
                              FlickrImageCrawler, GoogleImageCrawler,
                              GreedyImageCrawler, UrlListCrawler)


def test_google():
    google_crawler = GoogleImageCrawler(
        downloader_threads=4,
        storage={'root_dir': 'images/google'},
        log_level=logging.INFO)
    google_crawler.crawl(
        'cloudy',
        max_num=10,
        date_min=date(2016, 2, 1),
        date_max=date(2016, 3, 15))


def test_bing():
    bing_crawler = BingImageCrawler(
        storage={'root_dir': 'images/bing'}, log_level=logging.DEBUG)
    bing_crawler.crawl('sunny', max_num=10)


def test_baidu():
    baidu_crawler = BaiduImageCrawler(
        downloader_threads=4, storage={'root_dir': 'images/baidu'})
    baidu_crawler.crawl('bird', max_num=10)


def test_flickr():
    flickr_crawler = FlickrImageCrawler(
        apikey=None,
        downloader_threads=4,
        storage={'root_dir': 'images/flickr'})
    flickr_crawler.crawl(
        max_num=10,
        tags='family,child',
        tag_mode='all',
        group_id='68012010@N00')


def test_greedy():
    greedy_crawler = GreedyImageCrawler(
        parser_threads=4, storage={'root_dir': 'images/greedy'})
    greedy_crawler.crawl(
        'http://www.bbc.com/news', max_num=10, min_size=(100, 100))


def test_urllist():
    urllist_crawler = UrlListCrawler(
        downloader_threads=3, storage={'root_dir': 'images/urllist'})
    urllist_crawler.crawl('test_data/test_list.txt')


def main():
    if len(sys.argv) == 1:
        dst = 'all'
    else:
        dst = sys.argv[1:]
    if 'all' in dst:
        dst = ['google', 'bing', 'baidu', 'flickr', 'greedy', 'urllist']
    if 'google' in dst:
        test_google()
    if 'bing' in dst:
        test_bing()
    if 'baidu' in dst:
        test_baidu()
    if 'flickr' in dst:
        test_flickr()
    if 'greedy' in dst:
        test_greedy()
    if 'urllist' in dst:
        test_urllist()


if __name__ == '__main__':
    main()
