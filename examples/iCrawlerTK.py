# non-tk code is mostly from from iCrawler example(s)
# https://github.com/hellock/icrawler/

import os
import os.path as osp
import tempfile

import tkinter as tk
from tkinter import messagebox
from tkinter.messagebox import askyesno

import logging
from logging import config
import re
from yaml import safe_load

from icrawler.builtin import (
    BaiduImageCrawler,
    BingImageCrawler,
    FlickrImageCrawler,
    GoogleImageCrawler,
    GreedyImageCrawler,
    UrlListCrawler,
    Crawler,
)

from icrawler.utils import Session

from FilenameDownloader import FilenameDownloader
import GoogleLanguageOptions as lo

class MainApplication:

    global search_string # so the Enter() updates?

    def load_config(self):
        try:
            with open(self.config_file) as fconfig:
                config = safe_load(fconfig)
            print(self.config_file + ":")
            print(config)

            if "search_string" in config:
                self.search_string.set(config["search_string"])

            if "results" in config:
                self.results_value.set(config["results"])

            if "search_string_separator" in config:
                self.search_string_separator_value.set(config["search_string_separator"])
            else:
                self.search_string_separator_value.set(None)

            if "crawlers" in config:
                if "Google" in config["crawlers"] : self.crawlers_google.set(True)
                if "Bing" in config["crawlers"] : self.crawlers_bing.set(True)
                if "Baidu" in config["crawlers"] : self.crawlers_baidu.set(True)
                if "Flickr" in config["crawlers"] : self.crawlers_flickr.set(True)
                if "urllist" in config["crawlers"] : self.crawlers_urllist.set(True)
                if "refeed" in config["crawlers"] : self.crawlers_refeed.set(True)

            if "size" in config:
                self.size_value.set(config["size"])

            if "language" in config:
                self.language_value.set(config["language"])

            if "safe_mode" in config:
                if config["safe_mode"] == "On":
                    self.safe_mode.set(0)
                elif config["safe_mode"] == "Moderate":
                    self.safe_mode.set(43690)
                elif config["safe_mode"] == "Off":
                    self.safe_mode.set(65535)

        except Exception as e:
            self.logger.error(
                "Exception caught when loading config from %s, " "error: %s",
                self.config_file,
                e,
            )


    def __init__(self, master, *args, **kwargs):
        self.master = master
        self.frame = tk.Frame(master)
        self.config_file = "iCrawlerTK.yaml"
        logging.config.fileConfig("logging.conf")
        self.padding_size=10

        # add a VERBOSE logging option
        # TODO: https://stackoverflow.com/questions/9042919/python-logging-is-there-something-below-debug
        # logging.VERBOSE = int(logging.DEBUG / 2)
        # logging.addLevelName(logging.VERBOSE, "VERBOSE")
        # logging.Logger.verbose = lambda inst, msg, *args, **kwargs: inst.log(logging.VERBOSE, msg, *args, **kwargs)
        # logging.verbose = lambda msg, *args, **kwargs: logging.log(logging.VERBOSE, msg, *args, **kwargs)
        # add a VERBOSE logging option

        SIZE_OPTIONS = ["          ", "extralarge", "large", "medium", "small"]
        RESULTS_OPTIONS = ["10", "50", "100", "500", "1000"]
        LANGUAGE_OPTIONS = lo.google_language_dict.keys()

        self.crawlers_google = tk.BooleanVar()
        self.crawlers_bing = tk.BooleanVar()
        self.crawlers_baidu = tk.BooleanVar()
        self.crawlers_flickr = tk.BooleanVar()
        self.crawlers_urllist = tk.BooleanVar()
        self.crawlers_refeed = tk.BooleanVar()
        

        self.search_string = tk.StringVar()
        self.results_value = tk.StringVar(master)
        self.language_value = tk.StringVar(master)
        self.crawl_button_text=tk.StringVar(master)
        self.safe_mode = tk.IntVar()

        self.main_label = tk.Label(master, text="icrawler Options")
        self.search_string_label = tk.Label(master, text="Search For: ")
        self.search_string_entry = tk.Entry(master, textvariable=self.search_string)
        self.results_label = tk.Label(master, text="Results: ")
        self.size_value = tk.StringVar(master)
        self.crawlers_label = tk.Label(master, text="Crawlers: ")
        self.size_label = tk.Label(master, text="Size: ")
        self.language_label = tk.Label(master, text="Results Language: ")
        self.safe_mode_label = tk.Label(master, text="Safe Mode: ")

        self.results_options = tk.OptionMenu(master, self.results_value, *RESULTS_OPTIONS)
        self.results_options.config(takefocus=1)

        self.crawlers_frame = tk.Frame(master)
        tk.Checkbutton(self.crawlers_frame, text="Google", variable=self.crawlers_google).pack(anchor=tk.W)
        tk.Checkbutton(self.crawlers_frame, text="Bing", variable=self.crawlers_bing).pack(anchor=tk.W)
        tk.Checkbutton(self.crawlers_frame, text="Baidu", variable=self.crawlers_baidu).pack(anchor=tk.W)
        tk.Checkbutton(self.crawlers_frame, text="Flickr", variable=self.crawlers_flickr).pack(anchor=tk.W)
        tk.Checkbutton(self.crawlers_frame, text="source_urls.txt", variable=self.crawlers_urllist).pack(anchor=tk.W)
        tk.Checkbutton(self.crawlers_frame, text="Re-feed source pages", variable=self.crawlers_refeed).pack(anchor=tk.W)

        self.size_options = tk.OptionMenu(master, self.size_value, *SIZE_OPTIONS)

        self.safe_mode_frame = tk.Frame(master)
        tk.Radiobutton(self.safe_mode_frame, text="On", variable=self.safe_mode, value=0).pack(anchor=tk.W)
        tk.Radiobutton(self.safe_mode_frame, text="Medium", variable=self.safe_mode, value=43690).pack(anchor=tk.W)
        tk.Radiobutton(self.safe_mode_frame, text="Off", variable=self.safe_mode, value=65535).pack(anchor=tk.W)

        self.results_value.set(RESULTS_OPTIONS[0])
        self.size_value.set(SIZE_OPTIONS[0])

        self.main_label.grid(row=0, columnspan=2, padx=self.padding_size, pady=self.padding_size)

        self.search_string_label.grid(row=1, column=0, padx=self.padding_size, pady=self.padding_size)
        self.search_string_entry.grid(row=1, column=1, padx=self.padding_size, pady=self.padding_size)

        self.results_label.grid(row=2, column=0, padx=self.padding_size, pady=self.padding_size)
        self.results_options.config(takefocus=1)
        self.results_options.grid(row=2, column=1)

        self.crawlers_label.grid(row=3, column=0, padx=self.padding_size, pady=self.padding_size)
        self.crawlers_frame.grid(row=3, column=1, padx=self.padding_size, pady=self.padding_size)
        self.size_label.grid(row=4, column=0, padx=self.padding_size, pady=self.padding_size)

        self.size_options.grid(row=4, column=1)
        self.size_options.config(takefocus=1)

        self.safe_mode_label.grid(row=5, column=0, padx=self.padding_size, pady=self.padding_size)
        self.safe_mode_frame.grid(row=5, column=1, padx=self.padding_size, pady=self.padding_size)
        self.language_label.grid(row=6, column=0, padx=self.padding_size, pady=self.padding_size)

        # self.language_value.set("          ") # default value
        self.language_options = tk.OptionMenu(master, self.language_value, *LANGUAGE_OPTIONS )
        self.language_options.grid(row=6, column=1)
        self.language_options.config(takefocus=1)

        self.crawl_button_text.set("Go")
        self.crawl_button = tk.Button(master, command=self.go_clicked, textvariable=self.crawl_button_text)
        self.crawl_button.grid(row=7, columnspan=2, padx=self.padding_size, pady=self.padding_size)

        # options with config but no UI (yet)
        self.search_string_separator_value = tk.StringVar(master)

        self.load_config()

        def search_string_callback(e):
            # remove extra whitespace
            # search = " ".join(self.search_string.get().split())
            # alternate - also remove duplicate words
            search_string_t = " ".join(list(dict.fromkeys(self.search_string.get().split())))
            search_string_t = search_string_t.strip()
            if self.search_string.get() != search_string_t:
                self.search_string.set(search_string_t)
                print(search_string_t)

        self.search_string_entry.bind("<FocusOut>", search_string_callback)
        self.search_string_entry.focus_set()

        #end

    def go_clicked(self):

        threads=10 # TODO: set based on processor cores? 1/2 or 1/4 of available cores?

        max_number = int(self.results_value.get())

        search_string   =self.search_string.get()

        crawlers_baidu   =self.crawlers_baidu.get()
        crawlers_bing    =self.crawlers_bing.get()
        crawlers_flickr  =self.crawlers_flickr.get()
        crawlers_google  =self.crawlers_google.get()
        crawlers_urllist = self.crawlers_urllist.get()
        crawlers_refeed = self.crawlers_refeed.get()

        language = self.language_value.get().strip()

        search_crawlers = []
        if crawlers_baidu:
            search_crawlers.append("baidu")
        if crawlers_bing:
            search_crawlers.append("bing")
        if crawlers_google:
            search_crawlers.append("google")
        if crawlers_flickr:
            search_crawlers.append("flickr")
        if crawlers_urllist:
            search_crawlers.append("urllist")
        if crawlers_refeed:
            search_crawlers.append("refeed")

        if len(search_crawlers) < 1:
            tk.messagebox.showerror(title="iCrawler", message="No crawlers selected")
            return

        size = self.size_value.get()

        search_filters = {}

        safe_mode = self.safe_mode.get()
        
        if safe_mode == 65535: # all bits
            search_filters["safe"]="off"
        if safe_mode == 43690: # every other bit
            search_filters["safe"]="moderate"
        if safe_mode == 0:     # no bits
            search_filters["safe"]="on"

        #temp removal
        if "safe" in search_filters:
            del search_filters["safe"]

        if len(size.strip()) > 0:
            search_filters["size"]=size

        # TODO: colors search_filters["color"]=color
        # "red"
        # "orange"
        # "yellow"
        # "green"
        # "purple"
        # "pink"
        # "teal"
        # "blue"
        # "brown"
        # "white"
        # "black"
        # "blackandwhite"

        # search_filters ["date"]=((2023, 1, 1), (2023, 12, 1))

        if len(search_filters) < 1:
            search_filters = None

        if len(language) < 1:
            language = None

        print("\nSearch started: {} threads, maximum {} results, searching for '{}'".format(threads, max_number, search_string))
        print("Crawlers: {}".format(search_crawlers))
        print("Filters: {}\n".format(search_filters))
        print("Language: {}\n".format(language))

        # examples
        # search_filters = dict(size="large", date=(None, (2019, 1, 1)))
        # search_filters = dict(size="large")
        # search_filters = dict(type="photo", license="commercial", layout="wide", size="large", date="pastmonth")
        # search_filters = dict(size="large", color="blue")
        # search_filters = dict(size="extralarge")
        # search_filters = dict(size="=1600x1200")

        gText=self.crawl_button_text.get()
        self.crawl_button_text.set("Searching...")
        self.crawl_button.update_idletasks()

        search_terms = []
        if self.search_string_separator_value.get():
            search_terms = search_string.split(self.search_string_separator_value.get())
        else:
            search_terms.add(search_string)

        start_download(search_crawlers, search_terms, max_number, threads, language, search_filters, logging.DEBUG)

        self.crawl_button_text.set(gText)

        tk.messagebox.showinfo(title="iCrawler", message="Finished crawling.")


def start_download(search_crawlers, search_terms, max_number, threads, language, search_filters, log_level):

    # silence pillow extraneous info
    if log_level == logging.DEBUG:
        logging.getLogger('PIL').setLevel(logging.WARNING)

    # MonkeyPatch TODO: this should be before clicks happen, but it needs access to language.  Refactor this
    # https://web.archive.org/web/20120730014107/http://wiki.zope.org/zope2/MonkeyPatch
    def sub_set_session(self, headers=None):
        if headers is None:
            if language:
                accept_language="{};q=0.5, *;q=0.4".format(language)
            else:
                accept_language="*;q=0.4"

            # headers: google seems to like at least an accept-language, 
            #          and/or Accept-Encoding
            #          Baidu likes Brotli ("br"), which urllib3 supports

            headers = {
               "Accept-Language": accept_language,
               "Accept-Encoding": "deflate, gzip, br",
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
                    " AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/88.0.4324.104 Safari/537.36"
                )
            }
        elif not isinstance(headers, dict):
            raise TypeError('"headers" must be a dict object')

        self.session = Session(self.proxy_pool)
        self.session.headers.update(headers)

    Crawler.set_session = sub_set_session

    # def sub_set_logger(self, log_level=logging.INFO):
        # logging.config.fileConfig("logging.conf")
        # self.logger = logging.getLogger(__name__)
        # logging.getLogger("requests").setLevel(logging.WARNING)

    # Crawler.set_logger = sub_set_logger
    # MonkeyPatch

    for search_string in search_terms:
        # TODO: share this with FilenameDownloader and make it a config item
        search_folder_name = search_string.replace(" ", "_")
        search_folder_name = re.sub('[^a-zA-Z0-9_.-]', '', search_folder_name)


        #TODO: 
        #refeed_sourcefile = None
        #if "refeed" in search_crawlers:
        #    refeed_sourcefile = tempfile.NamedTemporaryFile("w", suffix="tmp", delete=False).name
        #this is a hack, creating GreedyImageCrawler so it calls set_storage()
        if "refeed" in search_crawlers:
            sourcefile = "refeed_source_urls.txt"
            if len(search_folder_name) < 1:
                search_folder_name = "RefeedUrls"
            storage={"root_dir": search_folder_name + "/refeed"}
            greedy_crawler = GreedyImageCrawler(downloader_threads=5, storage={"root_dir": search_folder_name + "/refeed"})
            if greedy_crawler.storage.exists(sourcefile):
                answer = askyesno(title='Confirmation', message='Overwrite source file refeed_source_urls.txt?')
                if answer != True:
                    tk.messagebox.showerror(title="iCrawler", message="Please delete refeed_source_urls.txt")
                    return

        if "google" in search_crawlers:

            # two char language or None
            if language in lo.google_language_dict:
                language=lo.google_language_dict[language]
            else:
                language=None

            print("\nstart GoogleImageCrawler")
            storage={"root_dir": search_folder_name + "/google"}
            google_crawler = GoogleImageCrawler(downloader_threads=threads, storage=storage, log_level=log_level, downloader_cls=FilenameDownloader)
            google_crawler.crawl(search_string, max_num=max_number, filters=search_filters, language=language)
            print("\nfinished GoogleImageCrawler\n")


        if  "bing" in search_crawlers:
            print("\nstart BingImageCrawler")
            storage={"root_dir": search_folder_name + "/bing"}
            bing_crawler = BingImageCrawler(downloader_threads=threads, storage=storage, log_level=log_level, downloader_cls=FilenameDownloader)
            bing_crawler.crawl(search_string, max_num=max_number, filters=search_filters)
            print("\nfinished BingImageCrawler\n")


        if "baidu" in search_crawlers:
            print("\nstart BaiduImageCrawler")
            storage={"root_dir": search_folder_name + "/baidu"}
            baidu_crawler = BaiduImageCrawler(downloader_threads=threads, storage=storage, log_level=log_level, downloader_cls=FilenameDownloader)
            baidu_crawler.crawl(search_string, max_num=max_number, filters=search_filters)
            print("\nfinished BaiduImageCrawler\n")


        # flickr crawler will error if there is no API key set
        if "flickr" in search_crawlers:
            print("\nstart FlickrImageCrawler")
            storage={"root_dir": search_folder_name + "/flickr"}
            flickr_crawler = FlickrImageCrawler(downloader_threads=threads, storage=storage, log_level=log_level)
            flickr_crawler.crawl(search_string, max_num=max_number, filters=search_filters)
            print("\nfinished FlickrImageCrawler")

            
        if "urllist" in search_crawlers:
            sourcefile = "source_urls.txt"
            if len(search_folder_name) < 1:
                search_folder_name = "SourceUrls"
            print("start GreedyImageCrawler")
            greedy_crawler = GreedyImageCrawler(downloader_threads=5, storage={"root_dir": search_folder_name + "/greedylist"})
            filename = osp.join(osp.dirname(__file__), sourcefile)
            with open(filename) as fin:
                filelist = [line.rstrip("\n") for line in fin]
            try:
                # make list unique, unordered
                # filelist = list(set(filelist))
                # python 3.7+
                count_before = len(filelist)
                filelist = list(dict.fromkeys(filelist))
                count_after = len(filelist)

                print("GreedyImageCrawler loaded {} urls, {} unique".format(count_before, count_after))
                greedy_crawler.crawl(filelist)
                print("\nfinished GreedyImageCrawler")
            except Exception as e:
                logging.getLogger().logger.error(
                    "GreedyImageCrawler exception: %s",
                    e
                )
            else:
                os.remove(sourcefile)


        if "refeed" in search_crawlers:
            sourcefile = "refeed_source_urls.txt"
            if len(search_folder_name) < 1:
                search_folder_name = "RefeedUrls"
            print("start GreedyImageCrawler")
            greedy_crawler = GreedyImageCrawler(downloader_threads=5, storage={"root_dir": search_folder_name + "/refeed"})
            filename = osp.join(osp.dirname(__file__), sourcefile)
            with open(filename) as fin:
                filelist = [line.rstrip("\n") for line in fin]
            try:
                # make list unique, unordered
                # filelist = list(set(filelist))
                # python 3.7+
                count_before = len(filelist)
                filelist = list(dict.fromkeys(filelist))
                count_after = len(filelist)

                print("GreedyImageCrawler loaded {} urls, {} unique".format(count_before, count_after))
                greedy_crawler.crawl(filelist)
                print("\nfinished GreedyImageCrawler")
            except Exception as e:
                logging.getLogger().logger.error(
                    "GreedyImageCrawler exception: %s",
                    e
                )
            else:
                os.remove(sourcefile)


def main():
    root = tk.Tk()
    root.title("iCrawlerTK")
    root.eval('tk::PlaceWindow . center')
    app = MainApplication(root)
    root.mainloop()

if __name__ == "__main__":
    main()
