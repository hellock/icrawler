# -*- coding: utf-8 -*-

import datetime
import json
import math
import os

from six.moves.urllib.parse import urlencode

from icrawler import Crawler, Feeder, Parser, ImageDownloader


class FlickrFeeder(Feeder):

    def feed(self,
             apikey=None,
             max_num=4000,
             page=1,
             user_id=None,
             tags=None,
             tag_mode='any',
             text=None,
             min_upload_date=None,
             max_upload_date=None,
             group_id=None,
             extras=None,
             per_page=100):
        if apikey is None:
            apikey = os.getenv('FLICKR_APIKEY')
            if not apikey:
                self.logger.error('apikey is not specified')
                return
        if max_num > 4000:
            max_num = 4000
            self.logger.warning(
                'max_num exceeds 4000, set it to 4000 automatically.')
        base_url = 'https://api.flickr.com/services/rest/?'
        params = {
            'method': 'flickr.photos.search',
            'api_key': apikey,
            'format': 'json',
            'nojsoncallback': 1
        }
        if user_id is not None:
            params['user_id'] = user_id
        if tags is not None:
            params['tags'] = tags
            params['tag_mode'] = tag_mode
        if text is not None:
            params['text'] = text
        if min_upload_date is not None:
            if isinstance(min_upload_date, datetime.date):
                params['min_upload_date'] = min_upload_date.strftime(
                    '%Y-%m-%d')
            elif isinstance(min_upload_date, (int, str)):
                params['min_upload_date'] = min_upload_date
            else:
                self.logger.error('min_upload_date is invalid')
        if max_upload_date is not None:
            if isinstance(min_upload_date, datetime.date):
                params['max_upload_date'] = max_upload_date.strftime(
                    '%Y-%m-%d')
            elif isinstance(min_upload_date, (int, str)):
                params['max_upload_date'] = max_upload_date
            else:
                self.logger.error('min_upload_date is invalid')
        if group_id is not None:
            params['group_id'] = group_id
        if extras is not None:
            params['extras'] = extras
        params['per_page'] = per_page
        url = base_url + urlencode(params)
        page_max = int(math.ceil(max_num / per_page))
        for i in range(page, page + page_max):
            complete_url = '{}&page={}'.format(url, i)
            self.output(complete_url)
            self.logger.debug('put url to url_queue: {}'.format(complete_url))


class FlickrParser(Parser):

    def parse(self, response):
        content = json.loads(response.content.decode())
        if content['stat'] != 'ok':
            return
        photos = content['photos']['photo']
        for photo in photos:
            farm_id = photo['farm']
            server_id = photo['server']
            photo_id = photo['id']
            secret = photo['secret']
            img_url = 'https://farm{}.staticflickr.com/{}/{}_{}.jpg'.format(
                farm_id, server_id, photo_id, secret)
            yield dict(file_url=img_url, meta=photo)


class FlickrImageCrawler(Crawler):

    def __init__(self, apikey=None, *args, **kwargs):
        self.apikey = apikey
        super(FlickrImageCrawler, self).__init__(
            feeder_cls=FlickrFeeder,
            parser_cls=FlickrParser,
            downloader_cls=ImageDownloader,
            *args,
            **kwargs)

    def crawl(self, max_num=1000, file_idx_offset=0, **kwargs):
        kwargs['apikey'] = self.apikey
        kwargs['max_num'] = max_num
        super(FlickrImageCrawler, self).crawl(
            feeder_kwargs=kwargs,
            downloader_kwargs=dict(
                max_num=max_num, file_idx_offset=file_idx_offset))
