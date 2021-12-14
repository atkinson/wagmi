import logging
import json
import math
from types import BuiltinMethodType

import ftx

from execution.exchanges import BaseExchange

# import http

# http.client.HTTPConnection.debuglevel = 1

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

    def _parse_symbol(self, market):
        """Remove the USD denominator from a Market.

        Some ftx calls need the market (pair), some only
        the coin.

        Args:
            market (str): the market, e.g. BTC/USD
        Returns:
            str: The symbol without the /USD e.g. BTC
        """
        if "/" in market:
            symbol = market.split("/")[0]
        return symbol

    def get_quote(self, market):
        """Get a quote

        Args:
            market (string): the market, e.g. 'BTC/USD'.

        Returns:
            dict: a dictionary result

        """
        # TODO check there is one and only one result?
        return self.client.get_market(market=market)

    def spot_is_borrowable(self, market):
        """Check if this spot market has lending (so you can short it).

        Args:
            market ([type]): [description]
        """
        info = self.client.get_market_info(market)
        if info[0].get("previousFunding"):
            return True

    def get_target_price(self, market, side, aggressive=False):
        """calculate a target price somewhere in the order book

        Args:
            market (string): [description]
            aggressive (bool, optional): [description]. Defaults to False.
        """
        assert not aggressive, "unsupported policy aggressive"
        quote = self.get_quote(market)
        return self._get_spread_midpoint(market, side)

    def _get_spread_midpoint(self, quote, side):
        """Compute target price to midpoint of the spread
        if possible (enough ticks in spread), else at best bid/offer

        Args:
            quote (object): quote data from API
            side (object): side
        """
        if not side == self.BUY and not side == self.SELL:
            raise NotImplementedError(f"Unsupported side: {side}")
        price_increment = quote.get("priceIncrement")
        bid = quote.get("bid")
        ask = quote.get("ask")
        assert bid <= ask, "invalid spread data"
        spread_in_ticks = (ask - bid) / price_increment

        if spread_in_ticks <= 1:
            return (
                bid if side == self.BUY else ask
            )  # can't do a midpoint on a spread of 1 tick, default to best bid/ask

        offset_ticks = math.ceil(spread_in_ticks / 2)
        offset_notional = offset_ticks * price_increment

        if side == self.BUY:
            target = bid + offset_notional
            if not (target < ask):
                raise AssertionError("invalid target price (side=buy)")
            return target
        if side == self.SELL:
            target = ask - offset_notional
            if not (target > bid):
                raise AssertionError("invalid target price (side=sell)")
            return target

    def get_tick_size(self, market):
        quote = self.get_quote(market)
        return quote.get("sizeIncrement")

    def _get_position(self, market: str):
        """[summary]

        Args:
            market ([type]): [description]

        Returns:
            [type]: [description]
        """
        spot_balances = self.client.get_balances()  # spot
        symbol = self._parse_symbol(market.name)
        positions = list(filter(lambda x: x["coin"] == symbol, spot_balances))
        if len(positions) == 1:
            retval = positions.pop().get("total")
            print(f"{market} has exactly one open position of size {retval}")
            return retval
        elif not len(positions):
            print(f"{market} does not have an open position")
            return 0.0
        else:
            raise IndexError(f"more than one position for {market} in {positions}")

    def set_position(self, market: str, target_position: float):
        """[summary]

        Args:
            market ([type]): [description]
            target_position ([type]): [description]
        """

        # TODO Need to consider if you can enter a short position on this security.
        current_position = self._get_position(market)

        delta = target_position - current_position

        if delta < 0:
            delta = abs(delta)
            self._place_order(market, self.SELL, delta)
        else:
            self._place_order(market, self.BUY, delta)

        # TODO
        # log whatgever you do.

    def _place_order(self, market: str, side: str, units: float):
        """[summary]

        Args:
            market ([type]): [description]
            side ([type]): [description]
            units ([type]): [description]
        """

        ### TODO Also need to check open orders....

        target_price = self.get_target_price(market, side)
        consideration = target_price * units

        tick = self.get_tick_size(market)

        print(
            f"""endpoint="executor",
            testmode="{self.testmode}"", 
            market="{market}",
            side="{side}",
            consideration="{consideration}",
            target_price="{target_price}",
            units="{units}" """
        )

        if units < tick:
            print(f"{market} order size {units} is less than the tick size {tick}")

        elif self.testmode == False:
            try:
                print(
                    self.client.place_order(
                        market=str(market),
                        side=side,
                        price=target_price,
                        size=units,
                        type="limit",
                        post_only=True,
                    )
                )
            except Exception as e:
                print("Exception!!")
                raise e
