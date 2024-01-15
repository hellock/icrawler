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
        # master.title("iCrawler")
        # master.geometry("{}x{}".format(460, 350))
        
        padding_size=7
        
        root.grid_rowconfigure(2, weight=1)
        root.grid_columnconfigure(1, weight=1)

        greeting = tk.Label(master, text="iCrawler Options")
        greeting.grid(row=0, columnspan=2, padx=padding_size, pady=padding_size)

        label_search_string = tk.Label(master, text="Search For: ")
        label_search_string.grid(row=1, column=0, padx=padding_size, pady=padding_size)
        
        # TODO: use a Text box and search each line as a keyword?
        entry_search_string = tk.Entry(master)
        entry_search_string.grid(row=1, column=1, padx=padding_size, pady=padding_size)

        label_crawlers = tk.Label(master, text="Crawlers: ")
        label_crawlers.grid(row=2, column=0, padx=padding_size, pady=padding_size)
        
        crawlers_frame = tk.Frame(master)
        crawlers_frame.grid(row=2, column=1, padx=padding_size, pady=padding_size)
        
        crawlers_google = tk.BooleanVar()
        tk.Checkbutton(crawlers_frame, text="Google", variable=crawlers_google).pack(anchor=tk.W)
        crawlers_bing = tk.BooleanVar()
        tk.Checkbutton(crawlers_frame, text="Bing", variable=crawlers_bing).pack(anchor=tk.W)
        crawlers_baidu = tk.BooleanVar()
        tk.Checkbutton(crawlers_frame, text="Baidu", variable=crawlers_baidu).pack(anchor=tk.W)
        

        crawl_button = tk.Button(master, text="Go")
        crawl_button.grid(row=3, columnspan=2, padx=padding_size, pady=padding_size)

# for frame app
# class MainApplication(tk.Frame):
    # def __init__(self, parent, *args, **kwargs):
        # self.frame = tk.Frame.__init__(self, parent, *args, **kwargs)
        # self.parent = parent
        # parent.title("iCrawler")
        # parent.geometry("{}x{}".format(460, 350))
        
        # greeting = tk.Label(self, text="iCrawler Options")
        # greeting.pack()

        # label_search_string = tk.Label(self, text="Search For: ")
        # label_search_string.pack()
        
        # # TODO: use a Text box and search each line as a keyword?
        # entry_search_string = tk.Entry(self)
        # entry_search_string.pack()

        # label_crawlers = tk.Label(self, text="Crawlers: ")
        # label_crawlers.pack()

def start_download(max_number, search_string, threads):

    # get from UI
    test_bing = True
    test_baidu = True
    test_google = True
    test_greedy = False
    test_urllist = False
    search_string = "TODO"
    search_folder_name = re.sub('[^a-zA-Z0-9_]', '', search_string)


    if test_google:
        print("start testing GoogleImageCrawler")
        google_crawler = GoogleImageCrawler(
            downloader_threads=threads, storage={"root_dir": search_folder_name + "/google"}, log_level=logging.INFO
        )
        # search_filters = dict(size="large", date=(None, (2019, 1, 1)))
        search_filters = dict(size="large")
        # search_filters = dict(size="=1600x1200")
        google_crawler.crawl(search_string, filters=search_filters, max_num=max_number)


    if  test_bing:
        print("start testing BingImageCrawler")
        bing_crawler = BingImageCrawler(downloader_threads=threads, storage={"root_dir": search_folder_name + "/bing"}, log_level=logging.INFO)
    #   search_filters = dict(type="photo", license="commercial", layout="wide", size="large", date="pastmonth")
        search_filters = dict(size="extralarge")
        bing_crawler.crawl(search_string, filters = search_filters, max_num=max_number)


    if test_baidu:
        print("start testing BaiduImageCrawler")
        search_filters = dict(size="large", color="blue")
        baidu_crawler = BaiduImageCrawler(downloader_threads=threads, storage={"root_dir": search_folder_name + "/baidu"})
        baidu_crawler.crawl(search_string, max_num=max_number)


    if test_greedy:
        print("start testing GreedyImageCrawler")
        greedy_crawler = GreedyImageCrawler(parser_threads=4, storage={"root_dir": search_folder_name + "/greedy"})
        greedy_crawler.crawl("http://www.bbc.com/news", max_num=10, min_size=(100, 100))


    if test_urllist:
        print("start testing UrlListCrawler")
        urllist_crawler = UrlListCrawler(downloader_threads=3, storage={"root_dir": search_folder_name + "/urllist"})
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
    root = tk.Tk()
    # for frame-based app
    # MainApplication(root).pack(side="top", fill="both", expand=True)
    # for tk-based app (non-frame)
    app = MainApplication(root)
    root.mainloop()
