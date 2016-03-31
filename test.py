# -*- coding: utf-8 -*-

from datetime import date
import sys
import logging
from image_crawler.examples import GoogleImageCrawler
from image_crawler.examples import BingImageCrawler
from image_crawler.examples import BaiduImageCrawler
from image_crawler.examples import FlickrImageCrawler


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
    flickr_crawler = FlickrImageCrawler('bc59c93a0c89a500f2ebe67d750219a8',
                                        'images/flickr')
    flickr_crawler.crawl(max_num=200, downloader_thr_num=4,
                         group_id='68012010@N00')


def main():
    if len(sys.argv) > 1:
        dest = sys.argv[1]
    else:
        dest = 'all'
    if dest == 'all':
        test_google()
        test_bing()
        test_baidu()
        test_flickr()
    elif dest == 'google':
        test_google()
    elif dest == 'bing':
        test_bing()
    elif dest == 'baidu':
        test_baidu()
    elif dest == 'flickr':
        test_flickr()


if __name__ == '__main__':
    main()
