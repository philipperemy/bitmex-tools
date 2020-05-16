import logging

from bitmex_tools.bitmex_ob_service import BitmexWaitForTick

logger = logging.getLogger(__name__)


def main():
    tick = BitmexWaitForTick()
    while True:
        print(tick.wait(max_seconds=1, up_tick=True), tick.bitmex_service.get_mp())


if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)12s - %(threadName)12s - %(name)18s - %(levelname)s - %(message)s')
    main()
