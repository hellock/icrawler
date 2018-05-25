Extend and write your own
=========================

It is easy to extend ``icrawler`` and use it to crawl other websites.
The simplest way is to override some methods of Feeder, Parser and Downloader class.

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
                           overwrite=False, **kwargs)

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