# -*- coding: utf-8 -*-

import datetime
import json
import math
import os

from six.moves.urllib.parse import urlencode

from icrawler import Crawler, Feeder, Parser, ImageDownloader


class FlickrFeeder(Feeder):

    def feed(self, apikey, max_num=4000, **kwargs):
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
                       'per_page', 'page',
                       'color_codes', 'styles', 'orientation']:  # yapf: disable
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
        page_max = int(math.ceil(4000.0 / per_page))
        for i in range(page, page + page_max):
            if self.signal.get('reach_max_num'):
                break
            complete_url = '{}&page={}'.format(url, i)
            while True:
                try:
                    self.output(complete_url, block=False)
                except:
                    if self.signal.get('reach_max_num'):
                        break
                else:
                    break
            self.logger.debug('put url to url_queue: {}'.format(complete_url))


class FlickrParser(Parser):

    def parse(self, response, apikey, size_preference=None):
        content = json.loads(response.content.decode('utf-8', 'ignore'))
        if content['stat'] != 'ok':
            return
        photos = content['photos']['photo']
        for photo in photos:
            photo_id = photo['id']
            base_url = 'https://api.flickr.com/services/rest/?'
            params = {
                'method': 'flickr.photos.getSizes',
                'api_key': apikey,
                'photo_id': photo_id,
                'format': 'json',
                'nojsoncallback': 1
            }
            try:
                ret = self.session.get(base_url + urlencode(params))
                info = json.loads(ret.content.decode())
            except:
                continue
            else:
                if info['stat'] == 'ok':
                    urls = {
                        item['label'].lower(): item['source']
                        for item in info['sizes']['size']
                    }
                else:
                    continue
                for sz in size_preference:
                    if sz in urls:
                        yield dict(file_url=urls[sz], meta=photo)
                        break


class FlickrImageCrawler(Crawler):

    def __init__(self,
                 apikey=None,
                 feeder_cls=FlickrFeeder,
                 parser_cls=FlickrParser,
                 downloader_cls=ImageDownloader,
                 *args,
                 **kwargs):
        if apikey is None:
            apikey = os.getenv('FLICKR_APIKEY')
            if not apikey:
                raise RuntimeError('apikey is not specified')
        self.apikey = apikey
        super(FlickrImageCrawler, self).__init__(
            feeder_cls, parser_cls, downloader_cls, *args, **kwargs)

    def crawl(self,
              max_num=1000,
              size_preference=None,
              min_size=None,
              max_size=None,
              file_idx_offset=0,
              overwrite=False,
              **kwargs):
        kwargs['apikey'] = self.apikey

        default_order = [
            'original', 'large 2048', 'large 1600', 'large', 'medium 800',
            'medium 640', 'medium', 'small 320', 'small', 'thumbnail',
            'large Square', 'square'
        ]
        if size_preference is None:
            size_preference = default_order
        elif isinstance(size_preference, str):
            assert size_preference in default_order
            size_preference = [size_preference]
        else:
            for sz in size_preference:
                assert sz in default_order
        super(FlickrImageCrawler, self).crawl(
            feeder_kwargs=kwargs,
            parser_kwargs=dict(
                apikey=self.apikey, size_preference=size_preference),
            downloader_kwargs=dict(
                max_num=max_num,
                min_size=min_size,
                max_size=max_size,
                file_idx_offset=file_idx_offset,
                overwrite=overwrite))
