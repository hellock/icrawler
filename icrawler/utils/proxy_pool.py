import json
import logging
import random
import threading
import time

import requests
from bs4 import BeautifulSoup

from six.moves import queue


class Proxy(object):
    """Proxy class

    Attributes:
        addr: A string with IP and port, for example '123.123.123.123:8080'.
        protocol: Either 'http' or 'https', indicating whether the proxy supports https.
        weight: A float point number indicating the probability of being
                selected, the weight is based on the connection time and stability.
        last_checked: A UNIX timestamp indicating when the proxy was checked.
    """

    def __init__(self,
                 addr=None,
                 protocol='http',
                 weight=1.0,
                 last_checked=None):
        self.addr = addr
        self.protocol = protocol
        self.weight = weight
        if last_checked is None:
            self.last_checked = int(time.time())
        else:
            self.last_checked = last_checked

    def format(self):
        """Return the proxy compatible with requests.Session parameters.

        Returns:
            A dictionary like {'http': '123.123.123.123:8080'}.
        """
        return {self.protocol: self.addr}

    def to_dict(self):
        """Return the proxy info in a dict"""
        return dict(
            addr=self.addr,
            protocol=self.protocol,
            weight=self.weight,
            last_checked=self.last_checked)


class ProxyPool(object):
    """Proxy pool implementation

    Attributes:
        idx: A dict containing two integer, indicating the index for http proxy
             list and https proxy list.
        test_url: A dict containing two urls, when testing a http proxy,
                  test_url['http'] will be used, otherwise test_url['https'] will be used.
        proxies: A dict containing all http and https proxies.
        addr_list: A dict containing all the address of proxies.
        dec_ratio: A float point number. When decreasing the weight of some
                   proxy, its weight is multiplied with `dec_ratio`
        inc_ratio: A float point number. Similar to `dec_ratio` but used for
                   increasing weights, default the reciprocal of `dec_ratio`
        weight_thr: A float point number indicating the minimum weight of a
                    proxy, if its weight is lower than `weight_thr`, it will
                    be removed from the proxy pool.
        logger: A logging.Logger object used for logging.
    """

    def __init__(self, filename=None):
        self.idx = {'http': 0, 'https': 0}
        self.test_url = {
            'http': 'http://www.sina.com.cn',
            'https': 'https://www.taobao.com'
        }
        self.proxies = {'http': {}, 'https': {}}
        self.addr_list = {'http': [], 'https': []}
        self.dec_ratio = 0.9
        self.inc_ratio = 1 / self.dec_ratio
        self.weight_thr = 0.2
        self.logger = logging.getLogger(__name__)
        if filename is not None:
            self.load(filename)

    def proxy_num(self, protocol=None):
        """ Get the number of proxies in the pool

        Args:
            protocol: 'http' or 'https' or None. (default None)

        Returns:
            If protocol is None, return the total number of proxies, otherwise,
            return the number of proxies of corresponding protocol.
        """
        http_num = len(self.proxies['http'])
        https_num = len(self.proxies['https'])
        if protocol == 'http':
            return http_num
        elif protocol == 'https':
            return https_num
        else:
            return http_num + https_num

    def get_next(self, protocol='http', format=False, policy='loop'):
        """
        Get the next proxy

        Args:
            protocol: 'http' or 'https'. (default 'http')
            format: A boolean indicating whether to format the proxy. (default False)
            policy: Either 'loop' or 'random', indicating the policy of getting
                    next proxy. If set to 'loop', will return proxies in turn,
                    otherwise will return a proxy randomly.

        Returns:
            If format is true, then return the formatted proxy which is
            compatible with requests.Session parameters, otherwise a Proxy object.
        """
        if not self.proxies[protocol]:
            return None
        if policy == 'loop':
            idx = self.idx[protocol]
            self.idx[protocol] = (idx + 1) % len(self.proxies[protocol])
        elif policy == 'random':
            idx = random.randint(0, self.proxy_num(protocol) - 1)
        else:
            self.logger.error('Unsupported get_next policy: {}'.format(policy))
            exit()
        proxy = self.proxies[protocol][self.addr_list[protocol][idx]]
        if proxy.weight < random.random():
            return self.get_next(protocol, format, policy)
        if format:
            return proxy.format()
        else:
            return proxy

    def save(self, filename):
        """Save proxies to file"""
        proxies = {'http': [], 'https': []}
        for protocol in ['http', 'https']:
            for proxy in self.proxies[protocol]:
                serializable_proxy = self.proxies[protocol][proxy].to_dict()
                proxies[protocol].append(serializable_proxy)
        with open(filename, 'w') as fout:
            json.dump(proxies, fout)

    def load(self, filename):
        """Load proxies from file"""
        with open(filename, 'r') as fin:
            proxies = json.load(fin)
        for protocol in proxies:
            for proxy in proxies[protocol]:
                self.proxies[protocol][proxy['addr']] = Proxy(
                    proxy['addr'], proxy['protocol'], proxy['weight'],
                    proxy['last_checked'])
                self.addr_list[protocol].append(proxy['addr'])

    def add_proxy(self, proxy):
        """Add a valid proxy into pool

        You must call `add_proxy` method to add a proxy into pool instead of
        directly operate the `proxies` variable.
        """
        protocol = proxy.protocol
        addr = proxy.addr
        if addr in self.proxies:
            self.proxies[protocol][addr].last_checked = proxy.last_checked
        else:
            self.proxies[protocol][addr] = proxy
            self.addr_list[protocol].append(addr)

    def remove_proxy(self, proxy):
        """Remove a proxy out of the pool"""
        del self.search_flag[proxy.protocol][proxy.addr]
        del self.addr_list[proxy.protocol][proxy.addr]

    def increase_weight(self, proxy):
        """Increase the weight of a proxy by multiplying inc_ratio"""
        new_weight = proxy.weight * self.inc_ratio
        if new_weight < 1.0:
            proxy.weight = new_weight
        else:
            proxy.weight = 1.0

    def decrease_weight(self, proxy):
        """Decreasing the weight of a proxy by multiplying dec_ratio"""
        new_weight = proxy.weight * self.dec_ratio
        if new_weight < self.weight_thr:
            self.remove_proxy(proxy)
        else:
            proxy.weight = new_weight

    def is_valid(self, addr, protocol='http', timeout=5):
        """Check if a proxy is valid

        Args:
            addr: A string in the form of 'ip:port'
            protocol: Either 'http' or 'https', different test urls will be used
                      according to protocol.
            timeout: A integer indicating the timeout of connecting the test url.

        Returns:
            A dict containing 2 fields.
            If the proxy is valid, returns {'valid': True, 'response_time': xx}
            otherwise returns {'valid': False, 'msg': 'xxxxxx'}
        """
        start = time.time()
        try:
            r = requests.get(self.test_url[protocol],
                             timeout=timeout,
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
                return {
                    'valid': False,
                    'msg': 'status code: {}'.format(r.status_code)
                }

    def validate(self,
                 proxy_scanner,
                 expected_num=20,
                 queue_timeout=3,
                 val_timeout=5):
        """Target function of validation threads

        Args:
            proxy_scanner: A ProxyScanner object.
            expected_num: Max number of valid proxies to be scanned.
            queue_timeout: Timeout for getting a proxy from the queue.
            val_timeout: An integer passed to `is_valid` as argument `timeout`.
        """
        while self.proxy_num() < expected_num:
            try:
                candidate_proxy = proxy_scanner.proxy_queue.get(
                    timeout=queue_timeout)
            except queue.Empty:
                if proxy_scanner.is_scanning():
                    continue
                else:
                    break
            addr = candidate_proxy['addr']
            protocol = candidate_proxy['protocol']
            ret = self.is_valid(addr, protocol, val_timeout)
            if self.proxy_num() >= expected_num:
                self.logger.info('Enough valid proxies, thread {} exit.'
                                 .format(threading.current_thread().name))
                break
            if ret['valid']:
                self.add_proxy(Proxy(addr, protocol))
                self.logger.info('{} ok, {:.2f}s'.format(addr, ret[
                    'response_time']))
            else:
                self.logger.info('{} invalid, {}'.format(addr, ret['msg']))

    def scan(self,
             proxy_scanner,
             expected_num=20,
             val_thr_num=4,
             queue_timeout=3,
             val_timeout=5,
             out_file='proxies.json'):
        """Scan and validate proxies

        Firstly, call the `scan` method of `proxy_scanner`, then using multi
        threads to validate them.

        Args:
            proxy_scanner: A ProxyScanner object.
            expected_num: Max number of valid proxies to be scanned.
            val_thr_num: Number of threads used for validating proxies.
            queue_timeout: Timeout for getting a proxy from the queue.
            val_timeout: An integer passed to `is_valid` as argument `timeout`.
            out_file: A string or None. If not None, the proxies will be saved
                      into `out_file`.
        """
        try:
            proxy_scanner.scan()
            self.logger.info('starting {} threads to validating proxies...'
                             .format(val_thr_num))
            val_threads = []
            for i in range(val_thr_num):
                t = threading.Thread(
                    name='val-{:0>2d}'.format(i + 1),
                    target=self.validate,
                    kwargs=dict(
                        proxy_scanner=proxy_scanner,
                        expected_num=expected_num,
                        queue_timeout=queue_timeout,
                        val_timeout=val_timeout))
                t.daemon = True
                val_threads.append(t)
                t.start()
            for t in val_threads:
                t.join()
            self.logger.info('Proxy scanning done!')
        except:
            raise
        finally:
            if out_file is not None:
                self.save(out_file)

    def default_scan(self,
                     region='mainland',
                     expected_num=20,
                     val_thr_num=4,
                     queue_timeout=3,
                     val_timeout=5,
                     out_file='proxies.json',
                     src_files=None):
        """Default scan method, to simplify the usage of `scan` method.

        It will register following scan functions:
        1. scan_file
        2. scan_cnproxy (if region is mainland)
        3. scan_free_proxy_list (if region is overseas)
        4. scan_ip84
        5. scan_mimiip
        After scanning, all the proxy info will be saved in out_file.

        Args:
            region: Either 'mainland' or 'overseas'
            expected_num: An integer indicating the expected number of proxies,
                          if this argument is set too great, it may take long to
                          finish scanning process.
            val_thr_num: Number of threads used for validating proxies.
            queue_timeout: An integer indicating the timeout for getting a
                           candidate proxy from the queue.
            val_timeout: An integer indicating the timeout when connecting the
                         test url using a candidate proxy.
            out_file: the file name of the output file saving all the proxy info
            src_files: A list of file names to scan
        """
        if expected_num > 30:
            self.logger.warn('The more proxy you expect, the more time it '
                             'will take. It is highly recommended to limit the'
                             ' expected num under 30.')
        proxy_scanner = ProxyScanner()
        if src_files is None:
            src_files = []
        elif isinstance(src_files, str):
            src_files = [src_files]
        for filename in src_files:
            proxy_scanner.register_func(proxy_scanner.scan_file,
                                        {'src_file': filename})
        if region == 'mainland':
            proxy_scanner.register_func(proxy_scanner.scan_cnproxy, {})
        elif region == 'overseas':
            proxy_scanner.register_func(proxy_scanner.scan_free_proxy_list, {})
        proxy_scanner.register_func(proxy_scanner.scan_ip84,
                                    {'region': region,
                                     'page': 5})
        proxy_scanner.register_func(proxy_scanner.scan_mimiip,
                                    {'region': region,
                                     'page': 5})
        self.scan(proxy_scanner, expected_num, val_thr_num, queue_timeout,
                  val_timeout, out_file)


class ProxyScanner():
    """Proxy scanner class

    ProxyScanner focuses on scanning proxy lists from different sources.

    Attributes:
        proxy_queue: The queue for storing proxies.
        scan_funcs: Name of functions to be used in `scan` method.
        scan_kwargs: Arguments of functions
        scan_threads: A list of `threading.thread` object.
        logger: A `logging.Logger` object used for logging.
    """

    def __init__(self):
        self.proxy_queue = queue.Queue()
        self.scan_funcs = []
        self.scan_kwargs = []
        self.scan_threads = []
        self.logger = logging.getLogger(__name__)

    def register_func(self, func_name, func_kwargs):
        """Register a scan function

        Args:
            func_name: The function name of a scan function.
            func_kwargs: A dict containing arguments of the scan function.
        """
        self.scan_funcs.append(func_name)
        self.scan_kwargs.append(func_kwargs)

    def scan_ip84(self, region='mainland', page=1):
        """Scan candidate proxies from http://ip84.com

        Args:
            region: Either 'mainland' or 'overseas'.
            page: An integer indicating how many pages to be scanned.
        """
        self.logger.info('start scanning http://ip84.com for proxy list...')
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
                self.proxy_queue.put({'addr': addr, 'protocol': protocol})

    def scan_mimiip(self, region='mainland', page=1):
        """Scan candidate proxies from http://mimiip.com

        Args:
            region: Either 'mainland' or 'overseas'.
            page: An integer indicating how many pages to be scanned.
        """
        self.logger.info('start scanning http://mimiip.com for proxy list...')
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
                self.proxy_queue.put({'addr': addr, 'protocol': protocol})

    def scan_cnproxy(self):
        """Scan candidate (mainland) proxies from http://cn-proxy.com"""
        self.logger.info(
            'start scanning http://cn-proxy.com for proxy list...')
        response = requests.get('http://cn-proxy.com')
        soup = BeautifulSoup(response.content, 'lxml')
        tables = soup.find_all('table', class_='sortable')
        for table in tables:
            for tr in table.tbody.find_all('tr'):
                info = tr.find_all('td')
                addr = '{}:{}'.format(info[0].string, info[1].string)
                self.proxy_queue.put({'addr': addr, 'protocol': 'http'})

    def scan_free_proxy_list(self):
        """Scan candidate (overseas) proxies from http://free-proxy-list.net"""
        self.logger.info('start scanning http://free-proxy-list.net '
                         'for proxy list...')
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
            self.proxy_queue.put({'addr': addr, 'protocol': protocol})

    def scan_file(self, src_file):
        """Scan candidate proxies from an existing file"""
        self.logger.info('start scanning file {} for proxy list...'
                         .format(src_file))
        with open(src_file, 'r') as fin:
            proxies = json.load(fin)
        for protocol in proxies.keys():
            for proxy in proxies[protocol]:
                self.proxy_queue.put({
                    'addr': proxy['addr'],
                    'protocol': protocol
                })

    def is_scanning(self):
        """Return whether at least one scanning thread is alive"""
        for t in self.scan_threads:
            if t.is_alive():
                return True
        return False

    def scan(self):
        """Start a thread for each registered scan function to scan proxy lists"""
        self.logger.info('{0} registered scan functions, starting {0} threads '
                         'to scan candidate proxy lists...'
                         .format(len(self.scan_funcs)))
        for i in range(len(self.scan_funcs)):
            t = threading.Thread(
                name=self.scan_funcs[i].__name__,
                target=self.scan_funcs[i],
                kwargs=self.scan_kwargs[i])
            t.daemon = True
            self.scan_threads.append(t)
            t.start()
