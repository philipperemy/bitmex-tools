from time import sleep

from bitmex_tools.bitmex_ob_service import FastTickerBitmex


def main():
    ftb = FastTickerBitmex('XBTUSD')
    last_bbo = None
    while True:
        new_bbo = ftb.bbo()
        if new_bbo != last_bbo:
            last_bbo = new_bbo
            print(new_bbo)
        sleep(0.0001)


if __name__ == '__main__':
    main()
