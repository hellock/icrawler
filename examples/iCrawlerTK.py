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
import re

# for non-frame app
class MainApplication:


    def __init__(self, master, *args, **kwargs):
        self.master = master
        self.frame = tk.Frame(master)
        
        padding_size=10
        
        root.grid_rowconfigure(3, weight=1)
        root.grid_columnconfigure(1, weight=1)

        self.greeting = tk.Label(master, text="iCrawler Options")
        self.greeting.grid(row=0, columnspan=2, padx=padding_size, pady=padding_size)

        label_search_string = tk.Label(master, text="Search For: ")
        label_search_string.grid(row=1, column=0, padx=padding_size, pady=padding_size)
        
        # TODO: use a Text box and search each line as a keyword?
        self.search_string =tk.StringVar(root)
        entry_search_string = tk.Entry(master, textvariable=self.search_string)
        entry_search_string.grid(row=1, column=1, padx=padding_size, pady=padding_size)
        label_crawlers = tk.Label(master, text="Crawlers: ")
        label_crawlers.grid(row=2, column=0, padx=padding_size, pady=padding_size)
        
        crawlers_frame = tk.Frame(master)
        crawlers_frame.grid(row=2, column=1, padx=padding_size, pady=padding_size)
        
        self.crawlers_google = tk.BooleanVar()
        tk.Checkbutton(crawlers_frame, text="Google", variable=self.crawlers_google).pack(anchor=tk.W)
        self.crawlers_bing = tk.BooleanVar()
        tk.Checkbutton(crawlers_frame, text="Bing", variable=self.crawlers_bing).pack(anchor=tk.W)
        self.crawlers_baidu = tk.BooleanVar()
        tk.Checkbutton(crawlers_frame, text="Baidu", variable=self.crawlers_baidu).pack(anchor=tk.W)

        label_size = tk.Label(master, text="Size: ")
        label_size.grid(row=3, column=0, padx=padding_size, pady=padding_size)
        # TODO: =WxH
        # TODO: >WxH (does baidu do this?  Or fix Baidu's error message?
        SIZE_OPTIONS = ["          ", "extralarge", "large", "medium", "small"]
        self.size_value = tk.StringVar(master)
        self.size_value.set(SIZE_OPTIONS[0]) # default value
        self.size_options = tk.OptionMenu(master, self.size_value, *SIZE_OPTIONS)
        self.size_options.grid(row=3, column=1)
        self.size_options.config(takefocus=1)

        self.crawl_button_text=tk.StringVar(root)
        self.crawl_button_text.set("Go")
        self.crawl_button = tk.Button(master, command=self.go_clicked, textvariable=self.crawl_button_text)
        self.crawl_button.grid(row=4, columnspan=2, padx=padding_size, pady=padding_size)

    def go_clicked(self):

        max_number=10
        threads=10

        search_string   =self.search_string.get()
        crawlers_bing   =self.crawlers_bing.get()
        crawlers_baidu  =self.crawlers_baidu.get()
        crawlers_google =self.crawlers_google.get()

        gText=self.crawl_button_text.get()
        self.crawl_button_text.set("Searching...")
        self.crawl_button.update_idletasks()
        start_download(crawlers_bing, crawlers_baidu, crawlers_google, search_string, max_number, threads)
        self.crawl_button_text.set(gText)


def start_download(crawlers_bing, crawlers_baidu, crawlers_google, search_string, max_number, threads):

    search_string = search_string.replace(" ", "_")
    search_folder_name = re.sub('[^a-zA-Z0-9_]', '', search_string)


    if crawlers_google:
        print("start testing GoogleImageCrawler")
        google_crawler = GoogleImageCrawler(
            downloader_threads=threads, storage={"root_dir": search_folder_name + "/google"}, log_level=logging.INFO
        )
        # search_filters = dict(size="large", date=(None, (2019, 1, 1)))
        search_filters = dict(size="large")
        # search_filters = dict(size="=1600x1200")
        google_crawler.crawl(search_string, filters=search_filters, max_num=max_number)


    if  crawlers_bing:
        print("start testing BingImageCrawler")
        bing_crawler = BingImageCrawler(downloader_threads=threads, storage={"root_dir": search_folder_name + "/bing"}, log_level=logging.INFO)
    #   search_filters = dict(type="photo", license="commercial", layout="wide", size="large", date="pastmonth")
        search_filters = dict(size="extralarge")
        bing_crawler.crawl(search_string, filters = search_filters, max_num=max_number)


    if crawlers_baidu:
        print("start testing BaiduImageCrawler")
        search_filters = dict(size="large", color="blue")
        baidu_crawler = BaiduImageCrawler(downloader_threads=threads, storage={"root_dir": search_folder_name + "/baidu"})
        baidu_crawler.crawl(search_string, max_num=max_number)


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
    root = tk.Tk()
    root.eval('tk::PlaceWindow . center') # roughly accurate
    app = MainApplication(root)
    root.mainloop()
