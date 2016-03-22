# -*- coding: utf-8 -*-

import sys
import logging
from image_crawler.examples import GoogleImageCrawler
from image_crawler.examples import BingImageCrawler
from image_crawler.examples import BaiduImageCrawler


def test_google():
    google_crawler = GoogleImageCrawler('images/google', log_level=logging.INFO)
    google_crawler.crawl('cloudy', 10, 1, 1, 4)


def test_bing():
    bing_crawler = BingImageCrawler('images/bing')
    bing_crawler.crawl('sunny', 10, 1, 1, 4)


def test_baidu():
    baidu_crawler = BaiduImageCrawler('images/baidu')
    baidu_crawler.crawl('sunny', 10, 1, 1, 4)


def main():
    if len(sys.argv) > 1:
        dest = sys.argv[1]
    else:
        dest = 'all'
    if dest == 'all':
        test_google()
        test_bing()
        test_baidu()
    elif dest == 'google':
        test_google()
    elif dest == 'bing':
        test_bing()
    elif dest == 'baidu':
        test_baidu()


if __name__ == '__main__':
    main()
