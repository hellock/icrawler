"""Unit test is expected to be here, while we use some usage cases instead."""

import logging
import os.path as osp
import shutil
import tempfile

from icrawler.builtin import (BaiduImageCrawler, BingImageCrawler,
                              GoogleImageCrawler, GreedyImageCrawler,
                              UrlListCrawler)

test_dir = tempfile.mkdtemp()


def test_google():
    img_dir = osp.join(test_dir, 'google')
    google_crawler = GoogleImageCrawler(
        downloader_threads=2,
        storage={'root_dir': img_dir},
        log_level=logging.INFO)
    search_filters = dict(
        size='large',
        color='orange',
        license='commercial,modify',
        date=(None, (2017, 11, 30)))
    google_crawler.crawl('cat', filters=search_filters, max_num=5)
    shutil.rmtree(img_dir)


def test_bing():
    img_dir = osp.join(test_dir, 'bing')
    bing_crawler = BingImageCrawler(
        downloader_threads=2,
        storage={'root_dir': img_dir},
        log_level=logging.INFO)
    search_filters = dict(
        type='photo',
        license='commercial',
        layout='wide',
        size='large',
        date='pastmonth')
    bing_crawler.crawl('cat', max_num=5, filters=search_filters)
    shutil.rmtree(img_dir)


def test_baidu():
    img_dir = osp.join(test_dir, 'baidu')
    search_filters = dict(size='large', color='blue')
    baidu_crawler = BaiduImageCrawler(
        downloader_threads=2, storage={'root_dir': img_dir})
    baidu_crawler.crawl('cat', filters=search_filters, max_num=5)
    shutil.rmtree(img_dir)


def test_greedy():
    img_dir = osp.join(test_dir, 'greedy')
    greedy_crawler = GreedyImageCrawler(
        parser_threads=2, storage={'root_dir': img_dir})
    greedy_crawler.crawl(
        'http://www.bbc.com/news', max_num=5, min_size=(100, 100))
    shutil.rmtree(img_dir)


def test_urllist():
    img_dir = osp.join(test_dir, 'urllist')
    urllist_crawler = UrlListCrawler(
        downloader_threads=2, storage={'root_dir': img_dir})
    filelist = osp.join(
        osp.dirname(osp.dirname(__file__)), 'examples/filelist_demo.txt')
    urllist_crawler.crawl(filelist)
    shutil.rmtree(img_dir)
