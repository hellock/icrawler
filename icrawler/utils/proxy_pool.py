import os
import json
import logging
import time
from collections import OrderedDict
from random import randint

import requests
from bs4 import BeautifulSoup


class Proxy(object):

    def __init__(self, addr=None, protocol='http', weight=1.0,
                 last_checked=None):
        self.addr = addr
        self.protocol = protocol
        self.weight = weight
        if last_checked is None:
            self.last_checked = int(time.time())
        else:
            self.last_checked = last_checked

    def format(self):
        return {self.protocol: self.addr}

    def to_dict(self):
        return dict(addr=self.addr,
                    protocol=self.protocol,
                    weight=self.weight,
                    last_checked=self.last_checked)

    def improve_weight(self, ratio):
        self.weight *= ratio

    def reduce_weight(self, ratio):
        self.weight /= ratio


class ProxyPool(object):
    """Proxy pool implementation
    """

    def __init__(self, filename=None):
        self.idx = {'http': 0, 'https': 0}
        self.test_url = {'http': 'http://www.sina.com.cn',
                         'https': 'https://www.taobao.com'}
        self.proxies = {'http': {}, 'https': {}}
        self.current_proxy = None
        if filename is not None:
            self.load(filename)
        self.logger = logging.getLogger(__name__)

    def proxy_num(self, protocol=None):
        """ Get the number of proxies in the pool
        """
        http_num = len(self.proxies['http'])
        https_num = len(self.proxies['https'])
        if protocol == 'http':
            return http_num
        elif protocol == 'https':
            return https_num
        else:
            return {'http': http_num, 'https': https_num}

    def get_next(self, protocol='http', format=True):
        if not self.proxies[protocol]:
            return None
        idx = self.idx[protocol]
        proxy = self.proxies[protocol][idx]
        self.current_proxy = proxy
        self.idx[protocol] = (idx + 1) % len(self.proxies[protocol])
        if format:
            return proxy.format()
        else:
            return proxy

    def get_random(self, protocol='http', format=True):
        if not self.proxies[protocol]:
            return ''
        if protocol == 'http':
            idx = randint(0, self.proxy_num('http') - 1)
        elif protocol == 'https':
            idx = randint(0, self.proxy_num('https') - 1)
        proxy = self.proxies[protocol][idx]
        self.current_proxy = proxy
        if format:
            return proxy.format()
        else:
            return proxy

    def current_proxy(self, format=False):
        if format:
            return self.current_proxy.format()
        else:
            return self.current_proxy

    # def self_check(self):
    #     for protocol in self.proxies:
    #         self.logger.info('start testing {} proxies...'.format(protocol))
    #         for proxy in self.proxies[protocol]:
    #             ret = self.is_valid(proxy)
    #             if ret['valid']:
    #                 print('{} ok, {:.2f}s'.format(proxy.addr,
    #                                               ret['response_time']))
    #             else:
    #                 print('{} invalid, {}'.format(proxy.addr, ret['msg']))

    def save(self, filename):
        proxies = {'http': [], 'https': []}
        for protocol in ['http', 'https']:
            for proxy in self.proxies[protocol]:
                serializable_proxy = self.proxies[protocol][proxy].to_dict()
                proxies[protocol].append(serializable_proxy)
        with open(filename, 'w') as fout:
            json.dump(proxies, fout)

    def load(self, filename):
        with open(filename, 'r') as fin:
            proxies = json.load(fin)
        for protocol in proxies:
            for proxy in proxies[protocol]:
                self.proxies[protocol][proxy['addr']] = Proxy(
                    proxy['addr'],
                    proxy['protocol'],
                    proxy['weight'],
                    proxy['last_checked']
                )

    def add_proxy(self, proxy):
        protocol = proxy.protocol
        addr = proxy.addr
        if proxy.addr in self.proxies:
            self.proxies[protocol][addr].last_checked = proxy.last_checked
        else:
            self.proxies[protocol][addr] = proxy

    def remove_proxy(self, proxy):
        del self.search_flag[proxy.protocol][proxy.addr]

    def is_valid(self, addr, protocol='http', timeout=5):
        start = time.time()
        try:
            r = requests.get(self.test_url[protocol], timeout=timeout,
                             proxies={protocol: 'http://' + addr})
        except KeyboardInterrupt:
            raise
        except requests.exceptions.Timeout:
            return {'valid': False, 'msg': 'timeout'}
        except:
            return {'valid': False, 'msg': 'exception'}
        else:
            if r.status_code == 200:
                response_time = time.time() - start
                return {'valid': True, 'response_time': response_time}
            else:
                return {'valid': False,
                        'msg': 'status code: {}'.format(r.status_code)}

    def scan_single(self, addr, protocol):
        ret = self.is_valid(addr, protocol)
        if ret['valid']:
            self.add_proxy(Proxy(addr, protocol))
            self.logger.info('{} ok, {:.2f}s'.format(addr, ret['response_time']))
        else:
            self.logger.info('{} invalid, {}'.format(addr, ret['msg']))

    def scan_ip84(self, region='mainland', page=1):
        """Scan valid proxies from http://ip84.com
        """
        self.logger.info('start scanning http://ip84.com for valid proxies...')
        for i in range(1, page + 1):
            if region == 'mainland':
                url = 'http://ip84.com/dlgn/{}'.format(i)
            elif region == 'overseas':
                url = 'http://ip84.com/gwgn/{}'.format(i)
            else:
                url = 'http://ip84.com/gn/{}'.format(i)
            response = requests.get(url)
            soup = BeautifulSoup(response.content, 'lxml')
            table = soup.find('table', class_='list')
            for tr in table.find_all('tr'):
                if tr.th is not None:
                    continue
                info = tr.find_all('td')
                protocol = info[4].string.lower()
                addr = '{}:{}'.format(info[0].string, info[1].string)
                self.scan_single(addr, protocol)

    def scan_kuaidaili(self, region='mainland', page=1):
        """Scan valid proxies from http://kuaidaili.com
        """
        self.logger.info('start scanning http://kuaidaili.com for valid proxies...')
        headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X '
                                 '10_11_4) AppleWebKit/537.36 (KHTML, like '
                                 'Gecko) Chrome/49.0.2623.110 Safari/537.36',
                   'Host': 'www.kuaidaili.com',
                   'Referer': 'http://www.kuaidaili.com/free/'}
        for i in range(1, page + 1):
            if region == 'mainland':
                url = 'http://www.kuaidaili.com/free/inha/{}'.format(i)
            else:
                url = 'http://www.kuaidaili.com/free/outha/{}'.format(i)
            response = requests.get(url, headers=headers)
            soup = BeautifulSoup(response.content, 'lxml')
            table = soup.find('table',
                              class_='table table-bordered table-striped')
            for tr in table.tbody.find_all('tr'):
                info = tr.find_all('td')
                protocol = info[3].string.lower()
                addr = '{}:{}'.format(info[0].string, info[1].string)
                self.scan_single(addr, protocol)

    def scan_cnproxy(self):
        """Scan valid http proxies from http://cn-proxy.com"""
        self.logger.info('start scanning http://cn-proxy.com for valid proxies...')
        response = requests.get('http://cn-proxy.com')
        soup = BeautifulSoup(response.content, 'lxml')
        tables = soup.find_all('table', class_='sortable')
        for table in tables:
            for tr in table.tbody.find_all('tr'):
                info = tr.find_all('td')
                addr = '{}:{}'.format(info[0].string, info[1].string)
                self.scan_single(addr, 'http')

    def scan_file(self, src_file):
        with open(src_file, 'r') as fin:
            proxies = json.load(fin)
        for protocol in proxies.keys():
            for proxy in proxies[protocol]:
                self.scan_single(proxy['addr'], protocol)

    def scan(self, src='ip84', filename='proxies.txt', scan_args={}):
        if src == 'all':
            multi_src = ['ip84', 'kuaidaili', 'cnproxy']
        elif isinstance(src, str):
            multi_src = [src]
        elif isinstance(src, list):
            multi_src = list(OrderedDict.fromkeys(src))
        else:
            self.logger.error('invalid scan src argument.')
            return
        for src in multi_src:
            if src in scan_args:
                kwargs = scan_args[src]
            else:
                kwargs = {}
            if os.path.isfile(src):
                self.scan_file(src)
            elif src == 'ip84':
                self.scan_ip84(**kwargs)
            elif src == 'kuaidaili':
                self.scan_kuaidaili(**kwargs)
            elif src == 'cnproxy':
                self.scan_cnproxy()
            else:
                self.logger.warning('invalid scan src %s is ignored.', src)
        if filename is not None:
            self.save(filename)
