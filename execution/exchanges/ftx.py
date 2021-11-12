import logging
import json
 import math
from types import BuiltinMethodType

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
        # maybe we need a type for symbol/market
        if "/" in symbol:
            symbol = symbol.split("/")[0]
        return symbol

    def get_quote(self, market):
        """Get a quote

        Args:
            market (string): The ticker you want quoted.

        Returns:
            dict: a dictrionary, example below.

        {
            "name": "BTC-0628",
            "baseCurrency": null,
            "quoteCurrency": null,
            "quoteVolume24h": 28914.76,
            "change1h": 0.012,
            "change24h": 0.0299,
            "changeBod": 0.0156,
            "highLeverageFeeExempt": false,
            "minProvideSize": 0.001,
            "type": "future",
            "underlying": "BTC",
            "enabled": true,
            "ask": 3949.25,
            "bid": 3949,
            "last": 10579.52,
            "postOnly": false,
            "price": 10579.52,
            "priceIncrement": 0.25,
            "sizeIncrement": 0.0001,
            "restricted": false,
            "volumeUsd24h": 28914.76
        }

        """
        # TODO check there is one and only one reults
        return self.client.get_market().get("result")

    def get_target_price(self, market, side, aggressive=False):
        """calculate a target price somewhere in the order book

        Args:
            market (string): [description]
            aggressive (bool, optional): [description]. Defaults to False.
        """
        quote = self.get_quote(market)
        tick = quote.get("sizeIncrement")
        bid = quote.get("bid")
        ask = quote.get("ask")
        spread_in_ticks = (bid - ask) / tick
        offset = math.ceil(spread_in_ticks/2)

        if (side == self.BUY) and ((bid + offset) < ask):
            return bid + offset
        elif (side == self.BUY):
            return bid
        elif (side == self.SELL) and ((ask - offset) > bid):
            return ask - offset
        else:
            return ask

    def get_position(self, market):
        """[summary]

        Args:
            market ([type]): [description]

        Returns:
            [type]: [description]
        """
        market = self.get_quote(market)
        spot_balances = self.client.get_balances()  # spot
        positions = list(filter(lambda x: x["coin"] == market, spot_balances))
        return positions.pop().get("total")

    def set_position(self, market, units):
        """[summary]

        Args:
            market ([type]): [description]
            units ([type]): [description]
        """
        current_position = self.get_position(market)
        delta = current_position - units

        if delta < 0:
            self._place_order(market, self.SHORT, delta)
        else:
            self._place_order(market, self.LONG, delta)

        # TODO
        # log whatgever you do.

    def _place_order(self, market, side, units):
        """[summary]

        Args:
            market ([type]): [description]
            side ([type]): [description]
            units ([type]): [description]
        """
        target_price = self.get_target_price(market, side)

        logger.info(
            'endpoint="executor",'
            "testmode={}, "
            'market="{}", '
            'side="{}", '
            "price={:,.4f}, "
            "units={:,.4f}".format(self.testmode, market, side, target_price, units)
        )

        if not self.testmode:
            try:
                self.client.place_order(
                    market=market,
                    side=side,
                    price=target_price,
                    size=units,
                    type="limit",
                )
            except Exception as e:
                print(e)
