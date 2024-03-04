import datetime
import json
import re
import html

import six
from bs4 import BeautifulSoup

from .. import Crawler, Feeder, ImageDownloader, Parser
from .filter import Filter


class BingFeeder(Feeder):

    def get_filter(self):
        search_filter = Filter()

        # type filter
        def format_type(img_type):
            prefix = "+filterui:photo-"
            return prefix + "animatedgif" if img_type == "animated" else prefix + img_type

        type_choices = ["photo", "clipart", "linedrawing", "transparent", "animated"]
        search_filter.add_rule("type", format_type, type_choices)

        # color filter
        def format_color(color):
            prefix = "+filterui:color2-"
            if color == "color":
                return prefix + "color"
            elif color == "blackandwhite":
                return prefix + "bw"
            else:
                return prefix + "FGcls_" + color.upper()

        color_choices = [
            "color",
            "blackandwhite",
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
            if size in ["large", "medium", "small"]:
                return "+filterui:imagesize-" + size
            elif size == "extralarge":
                return "+filterui:imagesize-wallpaper"
            elif size.startswith(">"):
                wh = size[1:].split("x")
                assert len(wh) == 2
                return "+filterui:imagesize-custom_{}_{}".format(*wh)
            else:
                raise ValueError(
                    'filter option "size" must be one of the following: '
                    "extralarge, large, medium, small, >[]x[] "
                    "([] is an integer)"
                )

        search_filter.add_rule("size", format_size)

        # licence filter
        license_code = {
            "creativecommons": "licenseType-Any",
            "publicdomain": "license-L1",
            "noncommercial": "license-L2_L3_L4_L5_L6_L7",
            "commercial": "license-L2_L3_L4",
            "noncommercial,modify": "license-L2_L3_L5_L6",
            "commercial,modify": "license-L2_L3",
        }

        def format_license(license):
            return "+filterui:" + license_code[license]

        license_choices = list(license_code.keys())
        search_filter.add_rule("license", format_license, license_choices)

        # layout filter
        layout_choices = ["square", "wide", "tall"]
        search_filter.add_rule("layout", lambda x: "+filterui:aspect-" + x, layout_choices)

        # people filter
        people_choices = ["face", "portrait"]
        search_filter.add_rule("people", lambda x: "+filterui:face-" + x, people_choices)

          # date filter
        date_minutes = {"pastday": 1440, "pastweek": 10080, "pastmonth": 43200, "pastyear": 525600}

        def format_date(date):
            if isinstance(date, tuple):
                assert len(date) == 2
                date_range = []
                for date_ in date:
                    if date_ is None:
                        date_str = ""
                    elif isinstance(date_, (tuple, datetime.date)):
                        date_ = datetime.date(*date_) if isinstance(date_, tuple) else date_
                        date_str = (date.fromisoformat(date_) - datetime.date(1970,1,1)).days
                    else:
                        raise TypeError("date must be a tuple or datetime.date object")
                    date_range.append(date_str)
                return "filters=ex1:\"ez5_{}_{}\"".format(*date_range)
            else:
                return "+filterui:age-lt" + str(date_minutes[date])

        date_choices = list(date_minutes.keys())
        # search_filter.add_rule("date", format_date, date_choices)
        search_filter.add_rule("date", format_date)

        safe_code = {
            "on": "on,safeui:on",
            "off": "OFF",
            "moderate": "moderate",
        }

        # safe search filter
        def format_safe(safe):
            return "safe:" + safe_code[safe]

        safe_choices = list(safe_code.keys())
        search_filter.add_rule("safe", format_safe, safe_choices)

        return search_filter

    def feed(self, keyword, offset, max_num, filters=None):
        base_url = "https://www.bing.com/images/async?q={}&first={}"
        self.filter = self.get_filter()
        filter_str = self.filter.apply(filters)
        filter_str = "&qft=" + filter_str if filter_str else ""

        for i in range(offset, offset + max_num, 20):
            url = base_url.format(keyword, i) + filter_str
            self.out_queue.put(url)
            self.logger.debug(f"put url to url_queue: {url}")


class BingParser(Parser):

    def parse(self, response):
        soup = BeautifulSoup(response.content.decode("utf-8", "ignore"), "lxml")
        self.save_results("Bing", soup)
        image_divs = soup.find_all("div", class_="imgpt")

        try:
            for div in image_divs:
                js = (div.a["m"])
                j=json.loads(js)
                img_src = j['purl']
                file_url = j['murl']
                with open("source_urls.txt", "a") as myfile:
                    myfile.write(j['purl'])
                    myfile.write("\n")

                yield dict(file_url=file_url, img_src=img_src)

        except Exception as e:
            self.logger.error(e)
            self.logger.error(div)
            pass

        pattern = re.compile(r"murl\":\"(.*?)\.jpg")
        for div in image_divs:
            try:
                href_str = html.unescape(div.a["m"])
            except KeyError:
                continue
            match = pattern.search(href_str)
            if match:
                name = match.group(1) if six.PY3 else match.group(1).encode("utf-8")
                img_url = f"{name}.jpg"
                yield dict(file_url=img_url)


class BingImageCrawler(Crawler):
    def __init__(self, feeder_cls=BingFeeder, parser_cls=BingParser, downloader_cls=ImageDownloader, *args, **kwargs):
        super().__init__(feeder_cls, parser_cls, downloader_cls, *args, **kwargs)

    def crawl(
        self,
        keyword,
        filters=None,
        offset=0,
        max_num=1000,
        min_size=None,
        max_size=None,
        file_idx_offset=0,
        overwrite=False,
    ):
        if offset + max_num > 1000:
            if offset > 1000:
                self.logger.error("Offset cannot exceed 1000, otherwise you " "will get duplicated searching results.")
                return
            elif max_num > 1000:
                max_num = 1000 - offset
                self.logger.warning(
                    "Due to Bing's limitation, you can only "
                    'get the first 1000 result. "max_num" has '
                    "been automatically set to %d",
                    1000 - offset,
                )
        feeder_kwargs = dict(keyword=keyword, offset=offset, max_num=max_num, filters=filters)
        downloader_kwargs = dict(
            max_num=max_num, min_size=min_size, max_size=max_size, file_idx_offset=file_idx_offset, overwrite=overwrite
        )
        super().crawl(feeder_kwargs=feeder_kwargs, downloader_kwargs=downloader_kwargs)
