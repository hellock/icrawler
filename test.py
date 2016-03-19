# -*- coding: utf-8 -*-

import sys
from image_crawler.examples import GoogleImageCrawler
from image_crawler.examples import BingImageCrawler
from image_crawler.examples import BaiduImageCrawler


def test_google():
    google_crawler = GoogleImageCrawler('images/google')
    google_crawler.crawl('sunny', 1000, 1, 1, 4)


def test_bing():
    bing_crawler = BingImageCrawler('images/bing')
    bing_crawler.crawl(2, 4, max_num=10, keyword='cat')


def test_baidu():
    baidu_crawler = BaiduImageCrawler('images/baidu')
    baidu_crawler.crawl(1, 4, max_num=10, keyword='cat')


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
