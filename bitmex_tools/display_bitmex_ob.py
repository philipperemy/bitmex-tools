import os
from time import sleep

from bitmex_tools.bitmex_ob_service import BitmexOrderBookService


def run():
    os.system('clear')
    bitmex_service = BitmexOrderBookService()
    while True:
        print(bitmex_service.get_ratio())
        print(bitmex_service.get_mp())
        sleep(1)


if __name__ == "__main__":
    run()
