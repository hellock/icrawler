import json
import logging
import random
import time

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


class ProxyPool(object):
    """Proxy pool implementation
    """

    def __init__(self, filename=None):
        self.idx = {'http': 0, 'https': 0}
        self.test_url = {'http': 'http://www.sina.com.cn',
                         'https': 'https://www.taobao.com'}
        self.proxies = {'http': {}, 'https': {}}
        self.addr_list = {'http': [], 'https': []}
        self.ratio = 0.9
        self.weight_thr = 0.2
        self.logger = logging.getLogger(__name__)
        if filename is not None:
            self.load(filename)

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
            return http_num + https_num

    def get_next(self, protocol='http', format=False):
        if not self.proxies[protocol]:
            return None
        idx = self.idx[protocol]
        proxy = self.proxies[protocol][self.addr_list[protocol][idx]]
        if proxy.weight < random.random():
            return self.get_next(protocol, format)
        self.idx[protocol] = (idx + 1) % len(self.proxies[protocol])
        if format:
            return proxy.format()
        else:
            return proxy

    def get_random(self, protocol='http', format=False):
        if not self.proxies[protocol]:
            return ''
        if protocol == 'http':
            idx = random.randint(0, self.proxy_num('http') - 1)
        elif protocol == 'https':
            idx = random.randint(0, self.proxy_num('https') - 1)
        proxy = self.proxies[protocol][self.addr_list[protocol][idx]]
        if format:
            return proxy.format()
        else:
            return proxy

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
                self.addr_list[protocol].append(proxy['addr'])

    def add_proxy(self, proxy):
        protocol = proxy.protocol
        addr = proxy.addr
        if addr in self.proxies:
            self.proxies[protocol][addr].last_checked = proxy.last_checked
        else:
            self.proxies[protocol][addr] = proxy
            self.addr_list[protocol].append(addr)

    def remove_proxy(self, proxy):
        del self.search_flag[proxy.protocol][proxy.addr]
        del self.addr_list[proxy.protocol][proxy.addr]

    def increase_weight(self, proxy):
        new_weight = proxy.weight / self.ratio
        if new_weight < 1.0:
            proxy.weight = new_weight
        else:
            proxy.weight = 1.0

    def decrease_weight(self, proxy):
        new_weight = proxy.weight * self.ratio
        if new_weight < self.weight_thr:
            self.remove_proxy(proxy)
        else:
            proxy.weight = new_weight

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

    def scan_ip84(self, region='mainland', page=1, expected_num=20):
        """Scan valid proxies from http://ip84.com
        """
        self.logger.info('start scanning http://ip84.com for valid proxies...')
        proxy_list = {'addr': [], 'protocol': []}
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
                proxy_list['addr'].append(addr)
                proxy_list['protocol'].append(protocol)
                # self.scan_single(addr, protocol)
                # if self.proxy_num() >= expected_num:
                #     return

    def scan_mimiip(self, region='mainland', page=1, expected_num=20):
        """Scan valid http proxies from http://mimiip.com"""
        self.logger.info('start scanning http://mimiip.com for valid proxies...')
        proxy_list = {'addr': [], 'protocol': []}
        for i in range(1, page + 1):
            if region == 'mainland':
                url = 'http://www.mimiip.com/gngao/{}'.format(i)
            elif region == 'overseas':
                url = 'http://www.mimiip.com/hw/{}'.format(i)
            else:
                url = 'http://www.mimiip.com/gngao/{}'.format(i)
            response = requests.get(url)
            soup = BeautifulSoup(response.content, 'lxml')
            table = soup.find('table', class_='list')
            for tr in table.find_all('tr'):
                if tr.th is not None:
                    continue
                info = tr.find_all('td')
                protocol = info[4].string.lower()
                addr = '{}:{}'.format(info[0].string, info[1].string)
                proxy_list['addr'].append(addr)
                proxy_list['protocol'].append(protocol)
                # self.scan_single(addr, protocol)
                # if self.proxy_num() >= expected_num:
                #     return

    def scan_cnproxy(self, region='mainland', expected_num=20):
        """Scan valid http proxies from http://cn-proxy.com"""
        if region != 'mainland':
            return
        self.logger.info('start scanning http://cn-proxy.com for valid proxies...')
        response = requests.get('http://cn-proxy.com')
        soup = BeautifulSoup(response.content, 'lxml')
        tables = soup.find_all('table', class_='sortable')
        for table in tables:
            for tr in table.tbody.find_all('tr'):
                info = tr.find_all('td')
                addr = '{}:{}'.format(info[0].string, info[1].string)
                self.scan_single(addr, 'http')
                if self.proxy_num() >= expected_num:
                    return

    def scan_free_proxy_list(self, region='overseas', expected_num=20):
        """Scan valid http proxies from http://free-proxy-list.net"""
        if region != 'overseas':
            return
        self.logger.info('start scanning http://free-proxy-list.net '
                         'for valid proxies...')
        response = requests.get('http://free-proxy-list.net')
        soup = BeautifulSoup(response.content, 'lxml')
        table = soup.find('table', id='proxylisttable')
        for tr in table.tbody.find_all('tr'):
            info = tr.find_all('td')
            if info[4].string != 'elite proxy':
                continue
            if info[6].string == 'yes':
                protocol = 'https'
            else:
                protocol = 'http'
            addr = '{}:{}'.format(info[0].string, info[1].string)
            self.scan_single(addr, protocol)
            if self.proxy_num() >= expected_num:
                return

    def scan_file(self, src_file, expected_num=20):
        with open(src_file, 'r') as fin:
            proxies = json.load(fin)
        for protocol in proxies.keys():
            for proxy in proxies[protocol]:
                self.scan_single(proxy['addr'], protocol)
                if self.proxy_num() >= expected_num:
                    return

    def scan(self, region='mainland', expected_num=20, out_file='proxies.json',
             src_files=[]):
        """Scan valid proxies from multi-source

        It will scan proxies in the following order:
        1. src_files
        2. cnproxy
        3. ip84, page 1
        4. mimiip, page 1
        5. repeat 3 and 4 till page 5
        After scaning, all the proxy info will be saved in out_file.

        Args:
            region: Either 'mainland' or 'overseas'
            expected_num: An integer indicating the expected number of proxies,
                          if this argument is set too great, it may take long to
                          finish scaning process.
            out_file: the file name of the output file saving all the proxy info
            src_files: A list of file names to scan
        """
        if expected_num > 30:
            self.logger.warn('The more proxy you expect, the more time it '
                             'will take. It is highly recommended to limit the'
                             ' expected num under 30.')
        if isinstance(src_files, str):
            files = [src_files]
        else:
            files = src_files
        if files:
            for filename in files:
                self.scan_file(filename, expected_num)
        if self.proxy_num() >= expected_num:
            return
        try:
            if region == 'mainland':
                self.scan_cnproxy(region, expected_num)
            elif region == 'overseas':
                self.scan_free_proxy_list(region, expected_num)
                if self.proxy_num() >= expected_num:
                    return
            for page in range(1, 6):
                self.scan_ip84(region, page, expected_num)
                if self.proxy_num() >= expected_num:
                    return
                self.scan_mimiip(region, page, expected_num)
                if self.proxy_num() >= expected_num:
                    return
        except:
            raise
        finally:
            if out_file is not None:
                self.save(out_file)
