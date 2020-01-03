from datetime import datetime, timedelta
import time

from heapq import heappush, heappop

import pickle

import logging


logger = logging.Logger(__name__)


class Proxy:
    def __init__(self, address, port, source, proxy_type=None):
        self._address = address
        self._port = port
        self._source = source
        self._proxy_type = proxy_type
        self.countdown = None
        self.bad_request = 0

    def __str__(self):
        return f'{self._address}:{self._port}'

    def __repr__(self):
        return f'{self.__class__.__name__}("{self._address}", "{self._port}", "{self._source}")'

    def __lt__(self, other):
        if self.end_countdown():
            return True

        if other.end_countdown():
            return False

        if self.countdown is None and other.countdown is None:
            return True

        if self.countdown is None and other.countdown:
            return True
        if self.countdown and other.countdown is None:
            return False

        now = datetime.now()
        return self.countdown - now < other.countdown - now

    def cold(self, seconds):
        self.countdown = datetime.now() + timedelta(seconds=seconds)

    def bad_cold(self, seconds):
        self.cold(seconds)
        self.bad_request += 1

    def end_countdown(self):
        if not self.countdown or self.countdown - datetime.now() < timedelta(0):
            return True
        return False


class ProxyManager:
    def __init__(self, proxies, source):
        self.default_countdown = 30
        self.bad_countdown = 300
        self.bad_max = 5
        self._source = source
        self._proxies = []
        self._file_name = f'proxies_{source}'
        self.add_proxies(proxies)

    def is_empty(self):
        if self._source:
            return False
        return True

    def save(self):
        logger.info(f'save proxy, {self._file_name}')
        with open(self._file_name, 'wb') as f:
            pickle.dump({self._source: self._proxies}, f)

    def load(self):
        logger.info(f'load proxy, {self._file_name}')
        with open(self._file_name) as f:
            self._proxies = pickle.load(f)[self._source]

    def clear(self, proxies=None):
        if proxies:
            proxies = set(proxies)
            for proxy in self._proxies:
                if str(proxy) in proxies:
                    self._proxies.pop(self._proxies.index(proxy))
        else:
            self._proxies = []

    def get_proxy(self):
        while not self.is_empty():
            proxy = heappop(self._proxies)
            if proxy.bad_request >= self.bad_max:
                logger.info(f'skip bad proxy, {str(proxy)}')
                continue
            proxy.cold(self.default_countdown)
            heappush(self._proxies, proxy)
            return proxy

    def cold_proxy(self, proxy_address):
        for proxy in self._proxies:
            if proxy_address in str(proxy):
                logger.info(f'cold proxy, {str(proxy)}')
                proxy.bad_cold(self.bad_countdown)

    def add_proxies(self, proxies):
        logger.info(f'add {len(proxies)} proxies')
        for i, proxy in enumerate(proxies):
            address, port = proxy.split(':')
            heappush(self._proxies, Proxy(address, port, self._source))

    def set_params(self, params):
        pass

    def statistics(self):
        return {str(proxy): proxy.bad_request for proxy in self._proxies}


if __name__ == '__main__':
    p1 = Proxy('addr', 8080, 'avito', 'sock4')
    p2 = Proxy('addr', 8080, 'avito', 'sock4')

    assert p1 > p2
    assert sorted([p2, p1]) == [p1, p2]

    p1.cold(10)

    assert p1 > p2
    assert sorted([p2, p1]) == [p2, p1]

    p1.countdown = None
    p2.cold(30)

    assert p1 < p2
    assert sorted([p2, p1]) == [p1, p2]
    p1.cold(15)

    assert p1 < p2
    assert sorted([p2, p1]) == [p1, p2]

    assert not p1.end_countdown()
    time.sleep(20)
    assert p1.end_countdown()
    print('done')
