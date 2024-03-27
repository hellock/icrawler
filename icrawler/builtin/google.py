import sys
import os
import datetime
import json
import hjson
import re
import logging
from urllib.parse import urlencode

from bs4 import BeautifulSoup

from .. import Crawler, Feeder, ImageDownloader, Parser
from .filter import Filter


class GoogleFeeder(Feeder):

    def get_filter(self):
        search_filter = Filter()

        # type filter
        def format_type(img_type):
            return "itp:lineart" if img_type == "linedrawing" else "itp:" + img_type

        type_choices = ["photo", "face", "clipart", "linedrawing", "animated"]
        search_filter.add_rule("type", format_type, type_choices)

        # color filter
        def format_color(color):
            if color in ["color", "blackandwhite", "transparent"]:
                code = {"color": "color", "blackandwhite": "gray", "transparent": "trans"}
                return "ic:" + code[color]
            else:
                return f"ic:specific,isc:{color}"

        color_choices = [
            "color",
            "blackandwhite",
            "transparent",
            "red",
            "orange",
            "yellow",
            "green",
            "teal",
            "blue",
            "purple",
            "pink",
            "white",
            "gray",
            "black",
            "brown",
        ]
        search_filter.add_rule("color", format_color, color_choices)

        # size filter
        def format_size(size):
            if size in ["large", "medium", "icon"]:
                size_code = {"large": "l", "medium": "m", "icon": "i"}
                return "isz:" + size_code[size]
            elif size.startswith(">"):
                size_code = {
                    "400x300": "qsvga",
                    "640x480": "vga",
                    "800x600": "svga",
                    "1024x768": "xga",
                    "2mp": "2mp",
                    "4mp": "4mp",
                    "6mp": "6mp",
                    "8mp": "8mp",
                    "10mp": "10mp",
                    "12mp": "12mp",
                    "15mp": "15mp",
                    "20mp": "20mp",
                    "40mp": "40mp",
                    "70mp": "70mp",
                }
                return "isz:lt,islt:" + size_code[size[1:]]
            elif size.startswith("="):
                wh = size[1:].split("x")
                assert len(wh) == 2
                return "isz:ex,iszw:{},iszh:{}".format(*wh)
            else:
                raise ValueError(
                    'filter option "size" must be one of the following: '
                    "large, medium, icon, >[]x[], =[]x[] ([] is an integer)"
                )

        search_filter.add_rule("size", format_size)

        # licence filter
        license_code = {
            "Commercial & other licenses": "ol",
            "Creative Commons licenses": "cl",
        }

        def format_license(license):
            return "il:" + license_code[license]

        license_choices = list(license_code.keys())
        search_filter.add_rule("license", format_license, license_choices)

        # date filter
        def format_date(date):
            if date == "anytime":
                return ""
            elif date == "pastday":
                return "qdr:d"
            elif date == "pastweek":
                return "qdr:w"
            elif date == "pastmonth":
                return "qdr:m"
            elif date == "pastyear":
                return "qdr:y"
            elif isinstance(date, tuple):
                assert len(date) == 2
                date_range = []
                for date_ in date:
                    if date_ is None:
                        date_str = ""
                    elif isinstance(date_, (tuple, datetime.date)):
                        date_ = datetime.date(*date_) if isinstance(date_, tuple) else date_
                        date_str = date_.strftime("%m/%d/%Y")
                    else:
                        raise TypeError("date must be a tuple or datetime.date object")
                    date_range.append(date_str)
                return "cdr:1,cd_min:{},cd_max:{}".format(*date_range)
            else:
                raise TypeError('filter option "date" must be "pastday", "pastweek" or ' "a tuple of dates")

        search_filter.add_rule("date", format_date)

        return search_filter

    def feed(self, keyword, offset, max_num, language=None, filters=None):
        base_url = "https://www.google.com/search?"
        self.filter = self.get_filter()
        filter_str = self.filter.apply(filters, sep=",")
        for i in range(offset, offset + max_num, 100):
            params = dict(q=keyword, ijn=int(i / 100), start=i, tbs=filter_str, tbm="isch")
            if language:
                params["lr"] = "lang_" + language
            url = base_url + urlencode(params)
            self.out_queue.put(url)
            self.logger.debug(f"put url to url_queue: {url}")


class GoogleParser(Parser):

    # Looking for <script> tags containing "AF_initDataCallback" and "ds:1"
    # unwanted example:
    #     AF_initDataCallback({key: 'ds:0', hash: '1', data:[], sideChannel: {}});
    # desired example:
    #     AF_initDataCallback({key: 'ds:1', hash: '2', data:[null,[null,null,nu...
    # 

    google_magic = "444383007" # "pDC"??? "D80"???

    def parse(self, response):
        soup = BeautifulSoup(response.content.decode("utf-8", "ignore"), "lxml")
        self.save_results("Google", soup)
        image_divs = soup.find_all(name="script")
        for div in image_divs:
            txt = str(div)
            if "AF_initDataCallback" not in txt:
                continue
            if "ds:0" in txt or "ds:1" not in txt:
                continue

            try:
                results = []
                start=txt.index("{")
                end = txt.index(");</script>", start)
                # hjson.loads is less strict than json.loads
                j = hjson.loads(txt[start:end])
                for i in j["data"][56][1][0][0][1][0]:
                    
                    if i[0][0][self.google_magic][0] == 1:
                        n = i[0][0][self.google_magic][1]
                        # if not n: might be an ad
                        if n:
                            img_src=n[25]["2003"][2]

                            self.logger.info("{}\n{}x{}".format(n[3][0], n[3][2], n[3][1]))
                            self.logger.info(img_src)
                            results.append(dict(file_url=n[3][0], img_src=img_src))
                            with open("refeed_source_urls.txt", "a") as myfile:
                                myfile.write(img_src)
                                myfile.write("\n")
                    elif i[0][0][self.google_magic][0] == 19:
                        self.logger.info("google magic {}{}".format(i[0][0][self.google_magic][0], i))
                    else:
                        self.logger.info("google magic unknown {}{}".format(i[0][0][self.google_magic][0], i))

                return results
            except Exception as e:
                self.logger.error(e)
                self.logger.error(txt[start:end])
                exc_type, exc_obj, exc_tb = sys.exc_info()
                fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                self.logger.error("%s\n%s\n%s", exc_type, fname, exc_tb.tb_lineno)
                pass

            uris = re.findall(r"http[^\[]*?\.(?:jpg|png|bmp)", txt)
            if len(uris) < 1:
                self.save_results(soup)
            return [{"file_url": uri} for uri in uris]


class GoogleImageCrawler(Crawler):
    def __init__(
        self, feeder_cls=GoogleFeeder, parser_cls=GoogleParser, downloader_cls=ImageDownloader, *args, **kwargs
    ):
        super().__init__(feeder_cls, parser_cls, downloader_cls, *args, **kwargs)

    def crawl(
        self,
        keyword,
        filters=None,
        offset=0,
        max_num=1000,
        min_size=None,
        max_size=None,
        language=None,
        file_idx_offset=0,
        overwrite=False,
    ):
        if offset + max_num > 1000:
            if offset > 1000:
                self.logger.error(
                    '"Offset" cannot exceed 1000, otherwise you will get ' "duplicated searching results."
                )
                return
            elif max_num > 1000:
                max_num = 1000 - offset
                self.logger.warning(
                    "Due to Google's limitation, you can only get the first "
                    '1000 result. "max_num" has been automatically set to %d. '
                    "If you really want to get more than 1000 results, you "
                    "can specify different date ranges.",
                    1000 - offset,
                )

        feeder_kwargs = dict(keyword=keyword, offset=offset, max_num=max_num, language=language, filters=filters)
        downloader_kwargs = dict(
            max_num=max_num, min_size=min_size, max_size=max_size, file_idx_offset=file_idx_offset, overwrite=overwrite
        )
        super().crawl(feeder_kwargs=feeder_kwargs, downloader_kwargs=downloader_kwargs)
