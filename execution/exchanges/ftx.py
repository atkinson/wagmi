import logging
import json

from django.conf import settings
import ftx

from execution.exchanges import BaseExchange

logger = logging.getLogger("execution")


class FTXExchange(BaseExchange):

    BUY = LONG = "buy"
    SELL = SHORT = "sell"

    def __init__(self, subaccount, testmode, api_key, api_secret) -> None:

        self.client = ftx.FtxClient(
            api_key=api_key, api_secret=api_secret, subaccount_name=subaccount
        )

        self.testmode = testmode
        logger.debug(f"ftx inited with testmode={testmode}")

    def parse_symbol(self, symbol):
        # remove /USD as ftx doesn't care for USD
        if "/" in symbol:
            symbol = symbol.split("/")[0]
        return symbol

    def get_position(self, market):
        market = self.parse_symbol(market)
        spot_balances = self.client.get_balances()  # spot
        positions = list(filter(lambda x: x["coin"] == market, spot_balances))
        return positions.pop().get("total")

    def set_position(self, market, units):
        current_position = self.get_position(market)
        delta = current_position - units

        # TODO: This needs to go somewhere else - we shouldn't have YOLO in this module.
        if abs(delta) > (settings.RW_YOLO_TRADE_BUFFER * current_position):
            if delta < 0:
                self._place_order(market, self.SHORT, delta)
        # TODO
        # log whatgever you do.

    def _place_order(self, market, side, units):
        latest = self.client.get_market(market)

        if side == self.BUY:
            limit = latest["ask"]  # * 0.9995
        else:
            limit = latest["bid"]  # * 1.0005

        logger.info(
            'endpoint="executor",'
            "testmode={}, "
            'market="{}", '
            'side="{}", '
            "price={:,.4f}, "
            "units={:,.4f}".format(self.testmode, market, side, limit, units)
        )

        if not self.testmode:
            try:
                self.client.place_order(
                    market=market,
                    side=side,
                    price=limit,
                    size=units,
                    type="limit",
                )
            except Exception as e:
                print(e)
