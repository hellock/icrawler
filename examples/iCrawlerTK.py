# non-tk code is mostly from from iCrawler example(s)
# https://github.com/hellock/icrawler/
import tkinter as tk
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


class start_window(tk.Frame):
    def __init__(self, parent=None):
        tk.Frame.__init__(self, parent)
        tk.Frame.pack(self)
        greeting = tk.Label(text="iCrawler Options")
        greeting.pack()


def start_download(max_number, search_string, threads):

    # get from UI
    test_bing = True
    test_baidu = True
    test_google = True
    test_greedy = False
    test_urllist = False
    search_string = "Lucy Hale best"


    if test_google:
        print("start testing GoogleImageCrawler")
        google_crawler = GoogleImageCrawler(
            downloader_threads=threads, storage={"root_dir": "images/google"}, log_level=logging.INFO
        )
        # search_filters = dict(size="large", date=(None, (2019, 1, 1)))
        search_filters = dict(size="large")
        # search_filters = dict(size="=1600x1200")
        # if "keeley" in search_string:
        #     search_filters = dict(size="=1920x1440")
        google_crawler.crawl(search_string, filters=search_filters, max_num=max_number)


    if  test_bing:
        print("start testing BingImageCrawler")
        bing_crawler = BingImageCrawler(downloader_threads=threads, storage={"root_dir": "images/bing"}, log_level=logging.INFO)
    #   search_filters = dict(type="photo", license="commercial", layout="wide", size="large", date="pastmonth")
        search_filters = dict(size="extralarge")
        bing_crawler.crawl(search_string, filters = search_filters, max_num=max_number)


    if test_baidu:
        print("start testing BaiduImageCrawler")
        search_filters = dict(size="large", color="blue")
        baidu_crawler = BaiduImageCrawler(downloader_threads=threads, storage={"root_dir": "images/baidu"})
        baidu_crawler.crawl(search_string, max_num=max_number)


    if test_greedy:
        print("start testing GreedyImageCrawler")
        greedy_crawler = GreedyImageCrawler(parser_threads=4, storage={"root_dir": "images/greedy"})
        greedy_crawler.crawl("http://www.bbc.com/news", max_num=10, min_size=(100, 100))


    if test_urllist:
        print("start testing UrlListCrawler")
        urllist_crawler = UrlListCrawler(downloader_threads=3, storage={"root_dir": "images/urllist"})
        filelist = osp.join(osp.dirname(__file__), "filelist_demo.txt")
        urllist_crawler.crawl(filelist)


def main():
    parser = ArgumentParser(description="Test built-in crawlers")

    parser.add_argument(
        "--crawler",
        nargs="+",
        default=["google", "bing", "baidu"],
        help="which crawlers to run",
    )
    parser.add_argument(
        "--search_string",
        nargs=1,
        default="Lucy Hale Hot & Sexy (19 Photos)",
        help="what to find",
    )
    parser.add_argument(
        "--max_number",
        nargs=1,
        default=1000,
        help="max results",
    )
    parser.add_argument(
        "--threads",
        nargs=1,
        default=9,
        help="number of threads",
    )

    args = parser.parse_args()

    print("max: {}\nsearch:{}\n".format(args.max_number, args.search_string))
        
    for crawler in args.crawler:
        eval(f"test_{crawler}({args.max_number}, \"{args.search_string}\", args.threads)")
        print("\n")


if __name__ == "__main__":
    window = tk.Tk()
    window.title("iCrawler")
    # window.geometry("500x400")
    app = start_window(window)
    window.mainloop()
