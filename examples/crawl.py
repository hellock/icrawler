import logging
import os.path as osp
from argparse import ArgumentParser

from icrawler.builtin import (
    BaiduImageCrawler,
    BingImageCrawler,
    FlickrImageCrawler,
    GoogleImageCrawler,
    GreedyImageCrawler,
    UrlListCrawler,
)


def test_google():
    print("start testing GoogleImageCrawler")
    google_crawler = GoogleImageCrawler(
        downloader_threads=4, storage={"root_dir": "images/google"}, log_level=logging.INFO
    )
    search_filters = dict(size="large", color="orange", license="commercial,modify", date=(None, (2017, 11, 30)))
    google_crawler.crawl("cat", filters=search_filters, max_num=10)


def test_bing():
    print("start testing BingImageCrawler")
    bing_crawler = BingImageCrawler(downloader_threads=2, storage={"root_dir": "images/bing"}, log_level=logging.INFO)
    search_filters = dict(type="photo", license="commercial", layout="wide", size="large", date="pastmonth")
    bing_crawler.crawl("cat", max_num=10, filters=search_filters)


def test_baidu():
    print("start testing BaiduImageCrawler")
    search_filters = dict(size="large", color="blue")
    baidu_crawler = BaiduImageCrawler(downloader_threads=4, storage={"root_dir": "images/baidu"})
    baidu_crawler.crawl("cat", filters=search_filters, max_num=10)


def test_flickr():
    print("start testing FlickrImageCrawler")
    flickr_crawler = FlickrImageCrawler(
        apikey=None, parser_threads=2, downloader_threads=4, storage={"root_dir": "images/flickr"}
    )
    flickr_crawler.crawl(max_num=10, tags="family,child", tag_mode="all", group_id="68012010@N00")


def test_greedy():
    print("start testing GreedyImageCrawler")
    greedy_crawler = GreedyImageCrawler(parser_threads=4, storage={"root_dir": "images/greedy"})
    greedy_crawler.crawl("http://www.bbc.com/news", max_num=10, min_size=(100, 100))


def test_urllist():
    print("start testing UrlListCrawler")
    urllist_crawler = UrlListCrawler(downloader_threads=3, storage={"root_dir": "images/urllist"})
    filelist = osp.join(osp.dirname(__file__), "filelist_demo.txt")
    urllist_crawler.crawl(filelist)


def main():
    parser = ArgumentParser(description="Test built-in crawlers")
    parser.add_argument(
        "--crawler",
        nargs="+",
        default=["google", "bing", "baidu", "flickr", "greedy", "urllist"],
        help="which crawlers to test",
    )
    args = parser.parse_args()
    for crawler in args.crawler:
        eval(f"test_{crawler}()")
        print("\n")


if __name__ == "__main__":
    main()
