import logging
import threading
from time import sleep, time

import numpy as np
import pandas as pd

from bitmex_tools.sockets.bitmex_socket_orderbook10 import BitMEXWebsocket as ob10
from bitmex_tools.sockets.bitmex_socket_orderbookL2 import BitMEXWebsocket as l2

logger = logging.getLogger(__name__)

ENDPOINT = 'wss://www.bitmex.com/realtime'


class FastTickerBitmex:

    def __init__(self, symbol):
        self.socket = l2(endpoint=ENDPOINT, symbol=symbol)
        while self.bbo() is None:
            sleep(0.001)

    def bbo(self):
        return self.socket.order_book_l2.bbo()


class BitmexWaitForTick:

    def __init__(self, bitmex_service=None):
        if bitmex_service is None:
            bitmex_service = BitmexOrderBookService()
        self.bitmex_service = bitmex_service

    def wait(self, max_seconds=5, up_tick=True, log=True):
        mp0 = self.bitmex_service.get_mp()
        start_time = time()
        if log:
            logger.info('Waiting for a tick...')
        while time() < start_time + max_seconds:
            mp1 = self.bitmex_service.get_mp()
            if up_tick and mp1 > mp0:
                return True, f'NEW: {mp1} > OLD: {mp0}'  # up tick!
            if not up_tick and mp1 < mp0:
                return True, f'NEW: {mp1} < OLD: {mp0}'  # down tick!
            sleep(0.01)
        return False, 'No ticks'  # nothing happened.


class BitmexOrderBookService:

    def __init__(self, symbol='XBTUSD', depth=5):
        self.cumsum_bid_volumes = None
        self.cumsum_ask_volumes = None
        self.a = None
        self.b = None
        self.ob = None
        self.mp = None
        self.symbol = symbol
        self.depth = depth
        self.thread = threading.Thread(target=self.run)
        self.thread.start()
        while self.get_ratio() is None or self.get_mp() is None:
            sleep(0.01)

    def get_mp(self):
        return 0.5 * self.get_best_bid() + 0.5 * self.get_best_ask()

    def get_best_bid(self):
        return self.b[0, 0]

    def get_best_ask(self):
        return self.a[0, 0]

    def get_bbo_volumes(self):
        return self.b[0, 1], self.a[0, 1]

    def get_ratio(self, depth=1):
        if self.cumsum_bid_volumes is None or self.cumsum_ask_volumes is None:
            return None
        assert 0 <= depth - 1 < len(self.cumsum_bid_volumes)
        return np.log(self.cumsum_bid_volumes[depth - 1]) - np.log(self.cumsum_ask_volumes[depth - 1])

    def get_ob(self):
        bids = np.transpose(np.vstack([self.b[:, 0], self.cumsum_bid_volumes]))
        asks = np.transpose(np.flip(np.vstack([self.a[:, 0], self.cumsum_ask_volumes]), axis=-1))

        order_book = np.vstack([asks, bids])
        order_book = pd.DataFrame(order_book, columns=['price', 'size'])
        order_book['side'] = ['Sell'] * 5 + ['Buy'] * 5

        return order_book.to_json(orient='records')

    def run(self):
        while True:
            try:
                ws = ob10(endpoint=ENDPOINT, symbol=self.symbol)
                while ws.ws.sock.connected:
                    try:
                        ob = ws.market_depth()
                        self.b = np.array(ob['bids'][0:self.depth])
                        self.a = np.array(ob['asks'][0:self.depth])
                        self.cumsum_bid_volumes = np.cumsum(self.b[:, 1])
                        self.cumsum_ask_volumes = np.cumsum(self.a[:, 1])
                        sleep(0.001)
                    except KeyError:  # socket not ready
                        sleep(0.1)
                        continue
            except AttributeError:  # socket no longer connected. Happens at 00:24.
                logger.exception('Received exception in the Bitmex WS.')
                sleep(10)
                logger.info('Trying to restart the WS...')
