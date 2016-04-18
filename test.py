# -*- coding: utf-8 -*-

import logging
import sys
from datetime import date

from icrawler.examples import GoogleImageCrawler
from icrawler.examples import BingImageCrawler
from icrawler.examples import BaiduImageCrawler
from icrawler.examples import FlickrImageCrawler
from icrawler.examples import GreedyImageCrawler


def test_google():
    google_crawler = GoogleImageCrawler('images/google', log_level=logging.INFO)
    google_crawler.crawl('cloudy', 0, 10, date(2016, 2, 1),
                         date(2016, 3, 15), 1, 1, 4)


def test_bing():
    bing_crawler = BingImageCrawler('images/bing')
    bing_crawler.crawl('sunny', 0, 10, 1, 1, 4)


def test_baidu():
    baidu_crawler = BaiduImageCrawler('images/baidu')
    baidu_crawler.crawl('sunny', 0, 10, 1, 1, 4)


def test_flickr():
    flickr_crawler = FlickrImageCrawler('your_own_apikey',
                                        'images/flickr')
    flickr_crawler.crawl(max_num=10, downloader_thr_num=4, tags='family,child',
                         tag_mode='all', group_id='68012010@N00')


def test_greedy():
    greedy_crawler = GreedyImageCrawler('images/greedy/')
    greedy_crawler.crawl('bbc.com/sport', 10, 4, 1, min_size=(200, 200))


def main():
    if len(sys.argv) == 1:
        dst = 'all'
    else:
        dst = sys.argv[1:]
    if 'all' in dst:
        dst = ['google', 'bing', 'baidu', 'flickr', 'greedy']
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


if __name__ == '__main__':
    main()
