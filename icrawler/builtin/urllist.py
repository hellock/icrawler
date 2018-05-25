import threading

from six.moves import queue

from icrawler import Crawler, Parser, UrlListFeeder, ImageDownloader


class PseudoParser(Parser):

    def worker_exec(self, queue_timeout=2, **kwargs):
        while True:
            if self.signal.get('reach_max_num'):
                self.logger.info('downloaded image reached max num, thread %s'
                                 ' exit',
                                 threading.current_thread().name)
                break
            try:
                url = self.in_queue.get(timeout=queue_timeout)
            except queue.Empty:
                if self.signal.get('feeder_exited'):
                    self.logger.info('no more page urls to parse, thread %s'
                                     ' exit',
                                     threading.current_thread().name)
                    break
                else:
                    self.logger.info('%s is waiting for new page urls',
                                     threading.current_thread().name)
                    continue
            except Exception as e:
                self.logger.error('exception caught in thread %s: %s',
                                  threading.current_thread().name, e)
                continue
            else:
                self.logger.debug('start downloading page {}'.format(url))
            self.output({'file_url': url})


class UrlListCrawler(Crawler):

    def __init__(self,
                 feeder_cls=UrlListFeeder,
                 parser_cls=PseudoParser,
                 downloader_cls=ImageDownloader,
                 *args,
                 **kwargs):
        super(UrlListCrawler, self).__init__(feeder_cls, parser_cls,
                                             downloader_cls, *args, **kwargs)

    def crawl(self, url_list, max_num=1000, file_idx_offset=0,
              overwrite=False):
        feeder_kwargs = dict(url_list=url_list)
        downloader_kwargs = dict(
            file_idx_offset=file_idx_offset,
            max_num=max_num,
            overwrite=overwrite)
        super(UrlListCrawler, self).crawl(
            feeder_kwargs=feeder_kwargs, downloader_kwargs=downloader_kwargs)
