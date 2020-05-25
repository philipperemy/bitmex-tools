import logging
from time import time

from sortedcontainers import SortedDict

logger = logging.getLogger(__name__)


class OrderBookL2:

    def __init__(self):
        self.bid_order_book = SortedDict()
        self.ask_order_book = SortedDict()
        self.ups = NumUpdatesPerSeconds()

    def fetch_queue(self, row):
        return self.bid_order_book if row['side'] == 'Buy' else self.ask_order_book

    def insert(self, row):
        book = self.fetch_queue(row)
        book[row['id']] = (row['size'], float(row['price']))

    def __str__(self):
        a = list(self.ask_order_book.values())
        b = list(self.bid_order_book.values())
        return f'{a}\n{b}\n{self.best_ask}\n{self.best_bid}\n--\n'

    def bbo(self):
        best_bid = self.best_bid
        best_ask = self.best_ask
        if best_bid is None or best_ask is None:
            return None
        assert best_bid <= best_ask
        return best_bid, best_ask

    @property
    def best_bid(self):
        try:
            return self.bid_order_book.peekitem(0)[-1][-1]
        except (IndexError, KeyError):
            return None

    @property
    def best_ask(self):
        try:
            return self.ask_order_book.peekitem(-1)[-1][-1]
        except (IndexError, KeyError):
            return None

    def update(self, row):
        book = self.fetch_queue(row)
        row_id = row['id']
        size, price = book[row_id]
        book[row_id] = (row['size'], price)

    def delete(self, row):
        book = self.fetch_queue(row)
        check1 = len(book)
        del book[row['id']]
        assert len(book) + 1 == check1

    def message(self, message):
        self.ups.count()
        action = message['action']
        data = message['data']
        for row in data:
            if action in ['partial', 'insert']:
                self.insert(row)
            elif action == 'update':
                self.update(row)
            elif action == 'delete':
                self.delete(row)
            else:
                raise Exception('Unknown action.')


class NumUpdatesPerSeconds:

    def __init__(self, max_num_updates=1000):
        self.c = 0
        self.max_num_updates = max_num_updates
        self.timer = None
        self.rate = 0
        self.timer = None

    def count(self):
        if self.c == 0:
            self.timer = time()
        self.c += 1
        if self.c == self.max_num_updates:
            self.rate = self.c / (time() - self.timer)
            self.c = 0


def main():
    order_book_l2 = OrderBookL2()

    snapshot = {
        "action": "partial",
        "data": [
            {"symbol": "XBTUSD", "id": 17999992000, "side": "Sell", "size": 100, "price": 80},
            {"symbol": "XBTUSD", "id": 17999993000, "side": "Sell", "size": 20, "price": 70},
            {"symbol": "XBTUSD", "id": 17999994000, "side": "Sell", "size": 10, "price": 60},
            {"symbol": "XBTUSD", "id": 17999995000, "side": "Buy", "size": 10, "price": 50},
            {"symbol": "XBTUSD", "id": 17999996000, "side": "Buy", "size": 20, "price": 40},
            {"symbol": "XBTUSD", "id": 17999997000, "side": "Buy", "size": 100, "price": 30}
        ]}

    update1 = {
        "action": "update",
        "data": [
            {"symbol": "XBTUSD", "id": 17999995000, "side": "Buy", "size": 5}
        ]}

    delete1 = {
        "action": "delete",
        "data": [
            {"symbol": "XBTUSD", "id": 17999995000, "side": "Buy"}
        ]}
    insert1 = {
        "action": "insert",
        "data": [
            {"symbol": "XBTUSD", "id": 17999995500, "side": "Buy", "size": 10, "price": 45},
        ]}

    print('snapshot')
    order_book_l2.message(snapshot)
    print(order_book_l2)

    print('update')
    order_book_l2.message(update1)
    print(order_book_l2)

    print('delete')
    order_book_l2.message(delete1)
    print(order_book_l2)

    print('insert')
    order_book_l2.message(insert1)
    print(order_book_l2)

    print(order_book_l2.ups.rate)


if __name__ == '__main__':
    main()
