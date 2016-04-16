import os
import time
import yaml
from random import randint

import requests
from bs4 import BeautifulSoup


class ProxyPool():
    """Proxy pool implementation
    """

    def __init__(self, filename=None):
        self.idx = {'http': 0, 'https': 0}
        self.test_url = {'http': 'http://www.sina.com.cn',
                         'https': 'https://www.taobao.com'}
        self.proxies = {'http': [], 'https': []}
        self.current_proxy = ''
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
            return {'http': http_num, 'https': https_num}

    def form_dict(self, proxy, protocol='http'):
        if proxy[:4] != 'http':
            proxy = 'http://' + proxy
        if protocol == 'https':
            return {'https': proxy}
        elif protocol == 'http':
            return {'http': proxy}

    def get_next(self, protocol='http', format=True):
        if not self.proxies[protocol]:
            return ''
        idx = self.idx[protocol]
        proxy = self.proxies[protocol][idx]
        self.current_proxy = proxy
        self.idx[protocol] = (idx + 1) % len(self.proxies[protocol])
        if format:
            proxy = self.form_dict(proxy)
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
            proxy = self.form_dict(proxy)
        return proxy

    def current_proxy(self, format=False):
        print(self.current_proxy)
        if format:
            return self.form_dict(self.current_proxy)
        else:
            return self.current_proxy

    def is_valid(self, proxy, protocol='http'):
        start = time.clock()
        try:
            r = requests.get(self.test_url[protocol.lower()], timeout=5,
                             proxies={protocol: 'http://' + proxy})
        except KeyboardInterrupt:
            raise
        except requests.exceptions.Timeout:
            return {'valid': False, 'msg': 'timeout'}
        except:
            return {'valid': False, 'msg': 'exception'}
        else:
            if r.status_code == 200:
                response_time = time.clock() - start
                return {'valid': True, 'response_time': response_time}
            else:
                return {'valid': False, 'msg': 'status code: {}'.format(r.status_code)}

    def test(self):
        for protocol in self.proxies:
            print('start testing {} proxies...'.format(protocol))
            for proxy in self.proxies[protocol]:
                ret = self.is_valid(proxy, protocol)
                if ret['valid']:
                    print('{} ok, {:.3}s'.format(proxy, ret['response_time']))
                else:
                    print('{} invalid, {}'.format(proxy, ret['msg']))

    def save(self, filename):
        with open(filename, 'w') as fout:
            fout.write(yaml.dump(self.proxies))

    def load(self, filename):
        with open(filename, 'r') as fin:
            self.proxies = yaml.load(fin)

    def scan_single(self, proxy, protocol):
        ret = self.is_valid(proxy, protocol)
        if ret['valid']:
            self.proxies[protocol].append(proxy)
            print('{} ok, {:.3}s'.format(proxy, ret['response_time']))
        else:
            print('{} invalid, {}'.format(proxy, ret['msg']))

    def scan_ip84(self, region='mainland', page=1):
        """Scan valid IP from http://ip84.com
        """
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
                proxy = '{}:{}'.format(info[0].string, info[1].string)
                self.scan_single(proxy, protocol)

    def scan_kuaidaili(self, region='mainland', page=1):
        """Scan valid IP from http://kuaidaili.com
        """
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
            with open('debug.html', 'w') as fout:
                fout.write(response.text)
            table = soup.find('table',
                              class_='table table-bordered table-striped')
            for tr in table.tbody.find_all('tr'):
                info = tr.find_all('td')
                protocol = info[3].string.lower()
                proxy = '{}:{}'.format(info[0].string, info[1].string)
                self.scan_single(proxy, protocol)

    def scan_file(self, src_file):
        with open(src_file, 'r') as fin:
            proxies = yaml.load(fin)
        for protocol in proxies.keys():
            for proxy in proxies[protocol]:
                ret = self.is_valid(proxy, protocol)
                if ret['valid']:
                    self.proxies[protocol].append(proxy)
                    print('{} ok, {:.3}s'.format(proxy, ret['response_time']))
                else:
                    print('{} invalid, {}'.format(proxy, ret['msg']))

    def scan(self, src='ip84', filename='proxies.txt', **kwargs):
        if os.path.isfile(src):
            self.scan_file(src)
        elif src == 'ip84':
            self.scan_ip84(**kwargs)
        elif src == 'kuaidaili':
            self.scan_kuaidaili(**kwargs)
        self.save(filename)
