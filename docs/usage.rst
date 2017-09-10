Basic usage
===========

Built-in crawlers
-----------------

This framework contains 6 built-in image crawlers.

-  Google
-  Bing
-  Baidu
-  Flickr
-  General greedy crawl (crawl all the images from a website)
-  UrlList (crawl all images given an url list)

Here is an example of how to use the built-in crawlers. The search
engine crawlers have similar interfaces.

.. code:: python

    from icrawler.builtin import BaiduImageCrawler, BingImageCrawler, GoogleImageCrawler

    google_crawler = GoogleImageCrawler(parser_threads=2, downloader_threads=4,
                                        storage={'root_dir': 'your_image_dir'})
    google_crawler.crawl(keyword='sunny', offset=0, max_num=1000,
                         date_min=None, date_max=None,
                         min_size=(200,200), max_size=None)
    bing_crawler = BingImageCrawler(downloader_threads=4,
                                    storage={'root_dir': 'your_image_dir'})
    bing_crawler.crawl(keyword='sunny', offset=0, max_num=1000,
                       min_size=None, max_size=None)
    baidu_crawler = BaiduImageCrawler(storage={'root_dir': 'your_image_dir'})
    baidu_crawler.crawl(keyword='sunny', offset=0, max_num=1000,
                        min_size=None, max_size=None)

.. note:: Only ``GoogleImageCrawler`` supports date range parameters, and it also allows specifying languages and filtering usage rights.

Flickr crawler is a little different.

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
-  ``tag_mode`` -- Either 'any' for an OR combination of tags, or 'all'
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

.. note::

    \* Before May 25th 2010 large photos only exist for very large original images.
    † Medium 800, large 1600, and large 2048 photos only exist after March 1st 2012.

``size_preference`` can be either a list or a string, if not specified, all
sizes are acceptable and larger sizes are prior to smaller ones. 

If you just want to crawl all the images from some website, then
``GreedyImageCrawler`` may be helpful.

.. code:: python

    from icrawler.builtin import GreedyImageCrawler

    greedy_crawler = GreedyImageCrawler(storage={'root_dir': 'your_image_dir'})
    greedy_crawler.crawl(domains='http://www.bbc.com/news', max_num=0, 
                         min_size=None, max_size=None)

The argument ``domains`` can be either an url string or list.

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

Write your own
--------------

It is easy to extend ``icrawler``. The simplest way is to override some
methods of Feeder, Parser and Downloader class.

1. **Feeder**

   The method you need to override is

   .. code:: python

       feeder.feed(self, **kwargs)

   If you want to offer the start urls at one time, for example from
   'http://example.com/page\_url/1' up to
   'http://example.com/page\_url/10'

   .. code:: python

       from icrawler import Feeder

       class MyFeeder(Feeder):
           def feed(self):
               for i in range(10):
                   url = 'http://example.com/page_url/{}'.format(i + 1)
                   self.output(url)

2. **Parser**

   The method you need to override is

   .. code:: python

       parser.parse(self, response, **kwargs)

   ``response`` is the page content of the url from ``url_queue``, what
   you need to do is to parse the page and extract file urls, and then
   put them into ``task_queue``. Beautiful Soup package is recommended
   for parsing html pages. Taking ``GoogleParser`` for example,

   .. code:: python

       class GoogleParser(Parser):

           def parse(self, response):
               soup = BeautifulSoup(response.content, 'lxml')
               image_divs = soup.find_all('div', class_='rg_di rg_el ivg-i')
               for div in image_divs:
                   meta = json.loads(div.text)
                   if 'ou' in meta:
                       yield dict(file_url=meta['ou'])

3. **Downloader**

   If you just want to change the filename of downloaded images, you can
   override the method

   .. code:: python

       downloader.get_filename(self, task, default_ext)

   The default names of downloaded files are increasing numbers, from
   000001 to 999999.

   Here is an example of using other filename formats instead of numbers as filenames.

   .. code:: python

        import base64

        from icrawler import ImageDownloader
        from icrawler.builtin import GoogleImageCrawler
        from six.moves.urllib.parse import urlparse


        class PrefixNameDownloader(ImageDownloader):

            def get_filename(self, task, default_ext):
                filename = super(PrefixNameDownloader, self).get_filename(
                    task, default_ext)
                return 'prefix_' + filename


        class Base64NameDownloader(ImageDownloader):

            def get_filename(self, task, default_ext):
                url_path = urlparse(task['file_url'])[2]
                if '.' in url_path:
                    extension = url_path.split('.')[-1]
                    if extension.lower() not in [
                            'jpg', 'jpeg', 'png', 'bmp', 'tiff', 'gif', 'ppm', 'pgm'
                    ]:
                        extension = default_ext
                else:
                    extension = default_ext
                # works for python 3
                filename = base64.b64encode(url_path.encode()).decode()
                return '{}.{}'.format(filename, extension)


        google_crawler = GoogleImageCrawler(
            downloader_cls=PrefixNameDownloader,
            # downloader_cls=Base64NameDownloader,
            downloader_threads=4,
            storage={'root_dir': 'images/google'})
        google_crawler.crawl('tesla', max_num=10)


   If you want to process meta data, for example save some annotations
   of the images, you can override the method

   .. code:: python

       downloader.process_meta(self, task):

   Note that your parser need to put meta data as well as file urls
   into ``task_queue``.

   If you want to do more with the downloader, you can also override the
   method

   .. code:: python

       downloader.download(self, task, default_ext, timeout=5, max_retry=3,
                           **kwargs)

   You can retrieve tasks from ``task_queue`` and then do what you want
   to do.

4. **Crawler**

   You can either use the base class ``Crawler`` or inherit from
   it. Two main apis are

   .. code:: python

       crawler.__init__(self, feeder_cls=Feeder, parser_cls=Parser,
                        downloader_cls=Downloader, feeder_threads=1,
                        parser_threads=1, downloader_threads=1,
                        storage={'backend': 'FileSystem', 'root_dir': 'images'},
                        log_level=logging.INFO)

   and

   .. code:: python

       crawler.crawl(self, feeder_kwargs={}, parser_kwargs={}, downloader_kwargs={})

   So you can use your crawler like this

   .. code:: python

       crawler = Crawler(feeder_cls=MyFeeder, parser_cls=MyParser,
                         downloader_cls=ImageDownloader, downloader_threads=4,
                         storage={'backend': 'FileSystem', 'root_dir': 'images'})
       crawler.crawl(feeder_kwargs=dict(arg1='blabla', arg2=0),
                     downloader_kwargs=dict(max_num=1000, min_size=None))

   Or define a class to avoid using complex and ugly dictionaries as
   arguments.

   .. code:: python

       class MyCrawler(Crawler):

           def __init__(self, *args, **kwargs):
               super(GoogleImageCrawler, self).__init__(
                   feeder_cls=MyFeeder,
                   parser_cls=MyParser,
                   downloader_cls=ImageDownloader,
                   *args,
                   **kwargs)

           def crawl(self, arg1, arg2, max_num=1000, min_size=None, max_size=None, file_idx_offset=0):
               feeder_kwargs = dict(arg1=arg1, arg2=arg2)
               downloader_kwargs = dict(max_num=max_num,
                                        min_size=None,
                                        max_size=None,
                                        file_idx_offset=file_idx_offset)
               super(MyCrawler, self).crawl(feeder_kwargs=feeder_kwargs,
                                            downloader_kwargs=downloader_kwargs)

       crawler = MyCrawler(downloader_threads=4,
                           storage={'backend': 'FileSystem', 'root_dir': 'images'})
       crawler.crawl(arg1='blabla', arg2=0, max_num=1000, max_size=(1000,800))
