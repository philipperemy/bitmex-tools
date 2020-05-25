import json
import logging
import math
import threading
import traceback
from time import sleep
from urllib.parse import urlunparse, urlparse

import websocket

from bitmex_tools.order_book_l2 import OrderBookL2

logger = logging.getLogger(__name__)


class BitMEXWebsocket:
    # Don't grow a table larger than this amount. Helps cap memory usage.
    MAX_TABLE_LEN = 200

    def __init__(self, endpoint, symbol, api_key=None, api_secret=None):
        """Connect to the websocket and initialize data stores."""
        logger.debug('Initializing WebSocket.')

        self.endpoint = endpoint
        self.symbol = symbol

        if api_key is not None and api_secret is None:
            raise ValueError('api_secret is required if api_key is provided')
        if api_key is None and api_secret is not None:
            raise ValueError('api_key is required if api_secret is provided')

        self.api_key = api_key
        self.api_secret = api_secret

        self.data = {}
        self.keys = {}
        self.exited = False

        self.order_book_l2 = OrderBookL2()

        # We can subscribe right in the connection querystring, so let's build that.
        # Subscribe to all pertinent endpoints
        wsURL = self.__get_url()
        logger.info('Connecting to %s' % wsURL)
        self.__connect(wsURL)
        logger.info('Connected to WS.')

    def exit(self):
        """Call this to exit - will close websocket."""
        self.exited = True
        self.ws.close()

    def get_instrument(self):
        """Get the raw instrument data for this symbol."""
        # Turn the 'tickSize' into 'tickLog' for use in rounding
        instrument = self.data['instrument'][0]
        instrument['tickLog'] = int(math.fabs(math.log10(instrument['tickSize'])))
        return instrument

    def __connect(self, wsURL):
        """Connect to the websocket in a thread."""
        logger.debug('Starting thread')

        self.ws = websocket.WebSocketApp(wsURL,
                                         on_message=self.__on_message,
                                         on_close=self.__on_close,
                                         on_open=self.__on_open,
                                         on_error=self.__on_error
                                         )

        self.wst = threading.Thread(target=lambda: self.ws.run_forever())
        self.wst.daemon = True
        self.wst.start()
        logger.debug('Started thread')

        # Wait for connect before continuing
        conn_timeout = 5
        while not self.ws.sock or not self.ws.sock.connected and conn_timeout:
            sleep(1)
            conn_timeout -= 1
        if not conn_timeout:
            logger.error('Couldnt connect to WS! Exiting.')
            self.exit()
            raise websocket.WebSocketTimeoutException('Couldnt connect to WS! Exiting.')

    def __get_url(self):
        """
        Generate a connection URL. We can define subscriptions right in the querystring.
        Most subscription topics are scoped by the symbol we're listening to.
        """

        # You can sub to orderBookL2 for all levels, or orderBookL2 for top 10 levels & save bandwidth
        symbolSubs = ['orderBookL2']
        genericSubs = ['margin']

        subscriptions = [sub + ':' + self.symbol for sub in symbolSubs]
        subscriptions += genericSubs

        urlParts = list(urlparse(self.endpoint))
        urlParts[0] = urlParts[0].replace('http', 'ws')
        urlParts[2] = '/realtime?subscribe={}'.format(','.join(subscriptions))
        return urlunparse(urlParts)

    def __wait_for_account(self):
        """On subscribe, this data will come down. Wait for it."""
        # Wait for the keys to show up from the ws
        while not {'margin', 'position', 'order', 'orderBookL2'} <= set(self.data):
            sleep(0.1)

    def __wait_for_symbol(self, symbol):
        """On subscribe, this data will come down. Wait for it."""
        while not {'instrument', 'trade', 'quote'} <= set(self.data):
            sleep(0.1)

    def __send_command(self, command, args=None):
        """Send a raw command."""
        if args is None:
            args = []
        self.ws.send(json.dumps({'op': command, 'args': args}))

    def __on_message(self, ws, message):
        message = json.loads(message)
        logger.debug(json.dumps(message))
        table = message['table'] if 'table' in message else None
        action = message['action'] if 'action' in message else None
        try:
            if 'subscribe' in message:
                logger.debug('Subscribed to %s.' % message['subscribe'])
            elif action:
                if table not in self.data:
                    self.data[table] = []
                self.order_book_l2.message(message)
        except:
            logger.error(traceback.format_exc())

    def __on_error(self, ws, error):
        """Called on fatal websocket errors. We exit on these."""
        if not self.exited:
            logger.error('Error : %s' % error)
            raise websocket.WebSocketException(error)

    def __on_open(self, ws):
        """Called when the WS opens."""
        logger.debug('Websocket Opened.')

    def __on_close(self, ws):
        """Called on websocket close."""
        logger.info('Websocket Closed')


if __name__ == '__main__':
    a = BitMEXWebsocket(endpoint='wss://www.bitmex.com/realtime', symbol='XBTUSD')
    last_bbo = None
    while True:
        new_bbo = a.order_book_l2.bbo()
        if new_bbo != last_bbo:
            last_bbo = new_bbo
            print(new_bbo)
        sleep(0.0001)
