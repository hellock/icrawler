Built-in crawlers
=================

This framework contains 6 built-in image crawlers.

-  Google
-  Bing
-  Baidu
-  Flickr
-  General greedy crawl (crawl all the images from a website)
-  UrlList (crawl all images given an url list)

Search engine crawlers
----------------------

The search engine crawlers (Google, Bing, Baidu) have universal APIs.
Here is an example of how to use the built-in crawlers. 

.. code:: python

    from icrawler.builtin import BaiduImageCrawler, BingImageCrawler, GoogleImageCrawler

    google_crawler = GoogleImageCrawler(
        feeder_threads=1,
        parser_threads=1,
        downloader_threads=4,
        storage={'root_dir': 'your_image_dir'})
    filters = dict(
        size='large',
        color='orange',
        license='commercial,modify',
        date=((2017, 1, 1), (2017, 11, 30)))
    google_crawler.crawl(keyword='cat', filters=filters, offset=0, max_num=1000,
                         min_size=(200,200), max_size=None, file_idx_offset=0)

    bing_crawler = BingImageCrawler(downloader_threads=4,
                                    storage={'root_dir': 'your_image_dir'})
    bing_crawler.crawl(keyword='cat', filters=None, offset=0, max_num=1000)

    baidu_crawler = BaiduImageCrawler(storage={'root_dir': 'your_image_dir'})
    baidu_crawler.crawl(keyword='cat', offset=0, max_num=1000,
                        min_size=(200,200), max_size=None)

The filter options provided by Google, Bing and Baidu are different.
Supported filter options and possible values are listed below.

GoogleImageCrawler:

- ``type`` -- "photo", "face", "clipart", "linedrawing", "animated".
- ``color`` -- "color", "blackandwhite", "transparent", "red", "orange", "yellow", "green", "teal", "blue", "purple", "pink", "white", "gray", "black", "brown".
- ``size`` -- "large", "medium", "icon", or larger than a given size (e.g. ">640x480"), or exactly is a given size ("=1024x768").
- ``license`` -- "noncommercial"(labeled for noncommercial reuse), "commercial"(labeled for reuse), "noncommercial,modify"(labeled for noncommercial reuse with modification), "commercial,modify"(labeled for reuse with modification).
- ``date`` -- "pastday", "pastweek" or a tuple of dates, e.g. ``((2016, 1, 1), (2017, 1, 1))`` or ``((2016, 1, 1), None)``.

BingImageCrawler:

- ``type`` -- "photo", "clipart", "linedrawing", "transparent", "animated".
- ``color`` -- "color", "blackandwhite", "red", "orange", "yellow", "green", "teal", "blue", "purple", "pink", "white", "gray", "black", "brown"
- ``size`` -- "large", "medium", "small" or larger than a given size (e.g. ">640x480").
- ``license`` -- "creativecommons", "publicdomain", "noncommercial", "commercial", "noncommercial,modify", "commercial,modify".
- ``layout`` -- "square", "wide", "tall".
- ``people`` -- "face", "portrait".
- ``date`` -- "pastday", "pastweek", "pastmonth", "pastyear".

BaiduImageCrawler:

- ``type``: "portrait", "face", "clipart", "linedrawing", "animated", "static"
- ``color``: "red", "orange", "yellow", "green", "purple", "pink", "teal", "blue", "brown", "white", "black", "blackandwhite".


When using ``GoogleImageCrawler``, language can be specified via the argument ``language``, e.g.,
``google_crawler.crawl(keyword='cat', language="us")``.

.. note::

    Tips: Search engines will limit the number of returned images, even when we use a browser
    to view the result page. The limitation is usually 1000 for many search engines such as google and bing. To crawl more than 1000 images with a single keyword, we can specify different date ranges.

    .. code:: python
    
        google_crawler.crawl(
            keyword='cat',
            filters={'date': ((2016, 1, 1), (2016, 6, 30))},
            max_num=1000,
            file_idx_offset=0)
        google_crawler.crawl(
            keyword='cat',
            filters={'date': ((2016, 6, 30), (2016, 12, 31))},
            max_num=1000,
            file_idx_offset='auto')
        # set `file_idx_offset` to "auto" so that filenames can be consecutive numbers (e.g., 1001 ~ 2000)


Flickr crawler
--------------

.. code:: python

    from datetime import date
    from icrawler.builtin import FlickrImageCrawler

    flickr_crawler = FlickrImageCrawler('your_apikey',
                                        storage={'root_dir': 'your_image_dir'})
    flickr_crawler.crawl(max_num=1000, tags='child,baby',
                         group_id='68012010@N00', min_upload_date=date(2015, 5, 1))

Supported optional searching arguments are listed in
https://www.flickr.com/services/api/flickr.photos.search.html.
Here are some examples.

-  ``user_id`` -- The NSID of the user who's photo to search.
-  ``tags`` -- A comma-delimited list of tags.
-  ``tag_mode`` -- Either "any" for an OR combination of tags, or "all"
   for an AND combination.
-  ``text`` -- A free text search. Photos who's title, description or
   tags contain the text will be returned.
-  ``min_upload_date`` -- Minimum upload date. The date can be in the
   form of ``datetime.date`` object, an unix timestamp or a string.
-  ``max_upload_date`` -- Maximum upload date. Same form as
   ``min_upload_date``.
-  ``group_id`` -- The id of a group who's pool to search.
-  ``extras`` -- A comma-delimited list of extra information to fetch
   for each returned record. See
   `here <https://www.flickr.com/services/api/flickr.photos.search.html>`__
   for more details.
-  ``per_page`` -- Number of photos to return per page.

Some advanced searching arguments, which are not updated in the `Flickr  API
<https://www.flickr.com/services/api/flickr.photos.search.html>`__,
are also supported. Valid arguments and values are shown as follows.

-  ``color_codes`` -- A comma-delimited list of color codes, which filters the
   results by your chosen color(s). Please see any Flickr search page for the
   corresponding relations between the colors and the codes.
-  ``styles`` -- A comma-delimited list of styles, including ``blackandwhite``,
   ``depthoffield``, ``minimalism`` and ``pattern``.
-  ``orientation`` -- A comma-delimited list of image orientation. It can be 
   ``landscape``, ``portrait``, ``square`` and ``panorama``. The default 
   includes all of them.

Another parameter ``size_preference`` is available for Flickr crawler, it define
the preferred order of image sizes. Valid values are shown as follows.

- original
- large 2048: 2048 on longest side†
- large 1600: 1600 on longest side†
- large: 1024 on longest side*
- medium 800: 800 on longest side†
- medium 640: 640 on longest side
- medium: 500 on longest side
- small 320: 320 on longest side
- small: 240 on longest side
- thumbnail: 100 on longest side
- large square: 150x150
- square: 75x75

``size_preference`` can be either a list or a string, if not specified, all
sizes are acceptable and larger sizes are prior to smaller ones. 

.. note::

    \* Before May 25th 2010 large photos only exist for very large original images.
    † Medium 800, large 1600, and large 2048 photos only exist after March 1st 2012.


Greedy crawler
--------------

If you just want to crawl all the images from some website, then
``GreedyImageCrawler`` may be helpful.

.. code:: python

    from icrawler.builtin import GreedyImageCrawler

    greedy_crawler = GreedyImageCrawler(storage={'root_dir': 'your_image_dir'})
    greedy_crawler.crawl(domains='http://www.bbc.com/news', max_num=0, 
                         min_size=None, max_size=None)

The argument ``domains`` can be either an url string or list.


URL list crawler
----------------

If you have already got an image url list somehow and want to download all
images using multiple threads, then ``UrlListCrawler`` may be helpful.

.. code:: python

    from icrawler.builtin import UrlListCrawler

    urllist_crawler = UrlListCrawler(downloader_threads=4,
                                     storage={'root_dir': 'your_image_dir'})
    urllist_crawler.crawl('url_list.txt')

You can see the complete example in *test.py*, to run it

::

    python test.py [options]

``options`` can be ``google``, ``bing`` , ``baidu``, ``flickr``,
``greedy``, ``urllist`` or ``all``, using ``all`` by default if no arguments are
specified. Note that you have to provide your flickr apikey if you want
to test FlickrCrawler.
