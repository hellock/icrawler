import logging
import threading

from six.moves import queue

from icrawler import Crawler, Feeder, Parser, UrlListFeeder


class UrlListParser(Parser):

    def thread_run(self, queue_timeout=2, request_timeout=5, max_retry=3,
                   task_threshold=50, **kwargs):
        while True:
            if self.global_signal.get('reach_max_num'):
                self.logger.info('downloaded image reached max num, thread %s'
                                 ' exit', threading.current_thread().name)
                break
            # get the page url
            try:
                url = self.url_queue.get(timeout=queue_timeout)
            except queue.Empty:
                if self.global_signal.get('feeder_exited'):
                    self.logger.info('no more page urls to parse, thread %s'
                                     ' exit', threading.current_thread().name)
                    break
                else:
                    self.logger.info('%s is waiting for new page urls',
                                     threading.current_thread().name)
                    continue
            except:
                self.logger.error('exception in thread %s',
                                  threading.current_thread().name)
                continue
            else:
                self.logger.debug('start downloading page {}'.format(url))
            self.put_task_into_queue({'img_url': url})


class UrlListCrawler(Crawler):

    def __init__(self, img_dir='images', log_level=logging.INFO):
        super(UrlListCrawler, self).__init__(
            img_dir, feeder_cls=UrlListFeeder,
            parser_cls=UrlListParser, log_level=log_level)

    def crawl(self, url_list, max_num=1000, feeder_thr_num=1, parser_thr_num=1,
              downloader_thr_num=1, save_mode='overwrite'):
        feeder_kwargs = dict(url_list=url_list)
        downloader_kwargs = dict(save_mode=save_mode, max_num=max_num)
        super(UrlListCrawler, self).crawl(
            feeder_thr_num, parser_thr_num, downloader_thr_num,
            feeder_kwargs=feeder_kwargs,
            downloader_kwargs=downloader_kwargs)
