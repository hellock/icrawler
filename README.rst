image\_crawler
==============

Introduction
------------

This python package is a mini framework of image crawlers. Python 2 is
not supported for the moment.

Stucture
--------

It consists of 3 main components (Feeder, Parser and Downloader) and 2
FIFO queues (url\_queue and task\_queue). The workflow is shown in the
following figure.

.. figure:: http://7xopqn.com1.z0.glb.clouddn.com/workflow.png
   :alt: 

-  ``url_queue`` stores the url of pages which may contain images
-  ``task_queue`` stores the image url as well as any meta data you
   like, each element in the queue is a dictionary and must contain the
   field ``img_url``
-  Feeder puts page urls to ``url_queue``
-  Parser requests and parses the page, then extracts the image urls and
   puts them into ``task_queue``
-  Downloader gets tasks from ``task_queue`` and requests the images,
   then saves them in the given path.

Feeder, parser and downloader supports multi-thread, so you can specify
the number of threads they use respectively.

Basic usage
-----------

Dependency installation
~~~~~~~~~~~~~~~~~~~~~~~

This framework use the HTTP library ``*requests*`` for sending requests
and the the parsing library ``*beautifulsoup4*`` for parsing HTML pages.
To install all the dependency using pip:

::

    pip install -r requirements.txt

Built-in crawlers
~~~~~~~~~~~~~~~~~

The framework has 3 built-in crawlers and all of them are search engine
crawlers (Google, Bing and Baidu). Here is an example of how to use the
built-in crawlers.

.. code:: python

    from image_crawler.examples import GoogleImageCrawler

    google_crawler = GoogleImageCrawler('images/google')
    google_crawler.crawl(keyword='sunny', offset=0, max_num=1000,
                         date_min=None, date_max=None, feeder_thr_num=1,
                         parser_thr_num=1, downloader_thr_num=4)

Run this code and the crawler will download the images in the search
result page using 1 thread to feed urls, 1 thread to parse the page and
4 threads to download the images.

You can see the complete example in *test.py*, to run it, simply

::

    python test.py [option]

``option`` can be ``google``, ``bing`` , ``baidu`` or ``all``, if not
specifed, ``all`` is used.

Other crawlers
~~~~~~~~~~~~~~

The simplest way is to overwrite some methods of the Feeder, Parser and
Downloader class.

1. Feeder

The method you need to overwrite is

.. code:: python

    feed(self, **kwargs)

If you want to offer the start urls at one time, for example
'http://example.com/page\_url/1' up to 'http://example.com/page\_url/10'

.. code:: python

    from image_crawler import Feeder

    class MyFeeder(Feeder):
        def feed(self):
            for i in range(10):
                url = 'http://example.com/page_url/{}'.format(i + 1)
                self.url_queue.put(url)

If the page urls is like search engine result urls, you can also use the
simple search engine feeder ``SimpleSEFeeder``, the api is like this

.. code:: python

    feed(self, url_template, keyword, offset, max_num, page_step)

Built-in crawlers are using ``SimpleSEFeeder`` as the feeder component.

2. Parser

The method you need to overwrite is

.. code:: python

    parse(self, response, **kwargs)

``response`` is the page content of the url from ``url_queue``, what you
need to do is to parse the page and find image urls, then put it to the
``task_queue``. Beautiful Soup package is suggested to be used for
parsing. Taking ``GoogleParser`` for example,

.. code:: python

    class GoogleParser(Parser):

        def parse(self, response):
            soup = BeautifulSoup(response, 'lxml')
            image_divs = soup.find_all('div', class_='rg_di rg_el ivg-i')
            pattern = re.compile(r'imgurl=(.*?)\.jpg')
            for div in image_divs:
                href_str = div.a['href']
                match = pattern.search(href_str)
                if match:
                    img_url = '{}.jpg'.format(match.group(1))
                    self.task_queue.put(dict(img_url=img_url))

3. Downloader

If you just want to change the filename of downloaded images, you can
overwrite the ``set_file_path()`` method:

.. code:: python

    set_file_path(self, img_task)

The default names of images are counting numbers, from 000001 to 999999.
If you want to do more with the downloader, you can also overwrite the
method:

.. code:: python

    download(self, img_task, request_timeout, **kwargs)

You can retrive tasks from ``task_queue`` and then do what you want to
do.

4. Crawler

You can either use the base class ``ImageCrawler`` or inherit from it.
Two main apis are:

.. code:: python

    __init__(self, img_dir='images', feeder_cls=Feeder, parser_cls=Parser,
                     downloader_cls=Downloader, log_level=logging.INFO)

and

.. code:: python

    crawl(self, feeder_thread_num=1, parser_thread_num=1,
                  downloader_thread_num=1, feeder_kwargs={},
                  parser_kwargs={}, downloader_kwargs={})

So you can use your crawler like this

.. code:: python

    crawler = Crawler(feeder_cls=SimpleSEFeeder, parser_cls=MyParser)
    crawler.crawl(feeder_thr_num=1, parser_thr_num=1, downloader_thr_num=4,
                  feeder_kwargs=dict(
                      url_template='https://www.some_search_engine.com/search?keyword={}&start={}',
                      keyword='cat',
                      offset=0,
                      max_num=1000,
                      page_step=50
                  ),
                  downloader_kwargs=dict(max_num=1000))

Or define a class to simplify the arguments.

.. code:: python

    class MySECrawler(Crawler):

        def __init__(self, img_dir='images', log_level=logging.INFO):
            ImageCrawler.__init__(self, img_dir, feeder_cls=SimpleSEFeeder,
                                  parser_cls=MyParser, log_level=log_level)

        def crawl(self, keyword, max_num, feeder_thr_num=1, parser_thr_num=1,
                  downloader_thr_num=1, offset=0):
            feeder_kwargs = dict(
                url_template='https://www.some_search_engine.com/search?keyword={}&start={}',
                keyword=keyword,
                offset=offset,
                max_num=max_num,
                page_step=50
            )
            downloader_kwargs = dict(max_num=max_num)
            super(MySECrawler, self).crawl(
                feeder_thr_num, parser_thr_num, downloader_thr_num,
                feeder_kwargs=feeder_kwargs,
                downloader_kwargs=downloader_kwargs)

    crawler = MySECrawler()
    crawler.crawl(keyword='cat', max_num=1000, feeder_thr_num=1,
                  parser_thr_num=1, downloader_thr_num=4, offset=0)
