icrawler
========

.. image:: https://img.shields.io/pypi/v/icrawler.svg
   :target: https://pypi.python.org/pypi/icrawler
   :alt: PyPI Version

.. image:: https://anaconda.org/hellock/icrawler/badges/version.svg
   :target: https://anaconda.org/hellock/icrawler
   :alt: Anaconda Version

.. image:: https://img.shields.io/pypi/pyversions/icrawler.svg
   :alt: Python Version

.. image:: 	https://img.shields.io/github/license/hellock/icrawler.svg
   :alt: License

Introduction
------------

Documentation: http://icrawler.readthedocs.io/

Try it with ``pip install icrawler`` or ``conda install -c hellock icrawler``.

This package is a mini framework of web crawlers. With modularization design,
it is easy to use and extend. It supports media data like images and videos
very well, and can also be applied to texts and other type of files.
Scrapy is heavy and powerful, while icrawler is tiny and flexible.

With this package, you can write a multiple thread crawler easily by focusing on
the contents you want to crawl, keeping away from troublesome problems like
exception handling, thread scheduling and communication.

It also provides built-in crawlers for popular image sites like **Flickr** and
search engines such as **Google**, **Bing** and **Baidu**.
(Thank all the contributors and pull requests are always welcome!)

Requirements
------------

Python 2.7+ or 3.5+ (recommended).

Examples
--------

Using built-in crawlers is very simple. A minimal example is shown as follows.

.. code:: python

    from icrawler.builtin import GoogleImageCrawler

    google_crawler = GoogleImageCrawler(storage={'root_dir': 'your_image_dir'})
    google_crawler.crawl(keyword='cat', max_num=100)

You can also configurate number of threads and apply advanced search options.
(Note: compatible with 0.6.0 and later versions)

.. code:: python

    from icrawler.builtin import GoogleImageCrawler

    google_crawler = GoogleImageCrawler(
        feeder_threads=1,
        parser_threads=2,
        downloader_threads=4,
        storage={'root_dir': 'your_image_dir'})
    filters = dict(
        size='large',
        color='orange',
        license='commercial,modify',
        date=((2017, 1, 1), (2017, 11, 30)))
    google_crawler.crawl(keyword='cat', filters=filters, max_num=1000, file_idx_offset=0)

For more advanced usage about built-in crawlers, please refer to the
`documentation <http://icrawler.readthedocs.io/en/latest/builtin.html>`_.

Writing your own crawlers with this framework is also convenient, see the
`tutorials <http://icrawler.readthedocs.io/en/latest/extend.html>`_.

Architecture
------------

A crawler consists of 3 main components (Feeder, Parser and Downloader),
they are connected with each other with FIFO queues. The workflow is shown in
the following figure.

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

Feeder, parser and downloader are all thread pools, so you can specify the
number of threads they use.
