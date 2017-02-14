# -*- coding: utf-8 -*-

import datetime
import json
import math
import os

from six.moves.urllib.parse import urlencode

from icrawler import Crawler, Feeder, Parser, ImageDownloader


class FlickrFeeder(Feeder):

    def feed(self, apikey=None, max_num=4000, **kwargs):
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
        for key in kwargs:
            if key in ['user_id', 'tags', 'tag_mode', 'text', 'license',
                       'sort', 'privacy_filter', 'accuracy', 'safe_search',
                       'content_type', 'machine_tags', 'machine_tag_mode',
                       'group_id', 'contacts', 'woe_id', 'place_id', 'has_geo',
                       'geo_context', 'lat', 'lon', 'radius', 'radius_units',
                       'is_commons', 'in_gallery', 'is_getty', 'extras',
                       'per_page', 'page']:  # yapf: disable
                params[key] = kwargs[key]
            elif key in ['min_upload_date', 'max_upload_date',
                         'min_taken_date', 'max_taken_date']:  # yapf: disable
                val = kwargs[key]
                if isinstance(val, datetime.date):
                    params[key] = val.strftime('%Y-%m-%d')
                elif isinstance(val, (int, str)):
                    params[key] = val
                else:
                    self.logger.error('%s is invalid', key)
            else:
                self.logger.error('Unrecognized search param: %s', key)
        url = base_url + urlencode(params)
        per_page = params.get('per_page', 100)
        page = params.get('page', 1)
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

    def __init__(self,
                 apikey=None,
                 feeder_cls=FlickrFeeder,
                 parser_cls=FlickrParser,
                 downloader_cls=ImageDownloader,
                 *args,
                 **kwargs):
        self.apikey = apikey
        super(FlickrImageCrawler, self).__init__(
            feeder_cls, parser_cls, downloader_cls, *args, **kwargs)

    def crawl(self, max_num=1000, file_idx_offset=0, **kwargs):
        kwargs['apikey'] = self.apikey
        kwargs['max_num'] = max_num
        super(FlickrImageCrawler, self).crawl(
            feeder_kwargs=kwargs,
            downloader_kwargs=dict(
                max_num=max_num, file_idx_offset=file_idx_offset))
