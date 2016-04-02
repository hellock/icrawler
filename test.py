# -*- coding: utf-8 -*-

from datetime import date
from icrawler.examples import GoogleImageCrawler
from icrawler.examples import BingImageCrawler
from icrawler.examples import BaiduImageCrawler
from icrawler.examples import FlickrImageCrawler
from icrawler.examples import GreedyImageCrawler
import logging
import sys


def test_google():
    google_crawler = GoogleImageCrawler('images/google', log_level=logging.INFO)
    google_crawler.crawl('cloudy', 0, 10, date(2016, 2, 1),
                         date(2016, 3, 15), 1, 1, 4)


def test_bing():
    bing_crawler = BingImageCrawler('images/bing')
    bing_crawler.crawl('sunny', 10, 1, 1, 4)


def test_baidu():
    baidu_crawler = BaiduImageCrawler('images/baidu')
    baidu_crawler.crawl('sunny', 10, 1, 1, 4)


def test_flickr():
    flickr_crawler = FlickrImageCrawler('your_own_apikey',
                                        'images/flickr')
    flickr_crawler.crawl(max_num=200, downloader_thr_num=4, tags='family,child',
                         tag_mode='all', group_id='68012010@N00')


def test_greedy():
    greedy_crawler = GreedyImageCrawler('images/iplaysoft')
    greedy_crawler.crawl('iplaysoft.com', 1000, 8, 2)


def main():
    if len(sys.argv) > 1:
        dst = sys.argv[1]
    else:
        dst = 'all'
    if dst == 'all':
        test_google()
        test_bing()
        test_baidu()
        test_flickr()
        test_greedy()
    elif dst == 'google':
        test_google()
    elif dst == 'bing':
        test_bing()
    elif dst == 'baidu':
        test_baidu()
    elif dst == 'flickr':
        test_flickr()
    elif dst == 'greedy':
        test_greedy()


if __name__ == '__main__':
    main()
