import logging
from time import sleep

from bitmex_tools.bitmex_ob_service import BitmexOrderBookService

logger = logging.getLogger(__name__)


def main():
    bit = BitmexOrderBookService(symbol='XBTU20')
    while True:
        # just for pretty printing.
        bid_volume, ask_volume = bit.get_bbo_volumes()
        log_volume_ratio = bit.get_ratio()
        if log_volume_ratio > 0:
            log_volume_ratio = f'+{log_volume_ratio:.3f}'
        else:
            log_volume_ratio = f'{log_volume_ratio:.3f}'
        print(f'BEST BID: {bit.get_best_bid()}| '
              f'BEST ASK: {bit.get_best_ask()}| '
              f'MID: {bit.get_mp()}| '
              f'BEST BID VOLUME: {int(bid_volume) // 1000:,}K| '
              f'BEST ASK VOLUME: {int(ask_volume) // 1000:,}K| '
              f'LOG VOLUME RATIO (DEPTH={bit.depth}): {log_volume_ratio}')
        sleep(1)


if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)12s - %(threadName)12s - %(name)18s - %(levelname)s - %(message)s')
    main()
