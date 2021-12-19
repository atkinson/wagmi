import logging
import json
import math
from types import BuiltinMethodType

import ftx

from execution.exchanges import BaseExchange

# import http

# http.client.HTTPConnection.debuglevel = 1

logger = logging.getLogger(__name__)


class FTXExchange(BaseExchange):
    BUY = LONG = "buy"
    SELL = SHORT = "sell"
    fiats = ['USD', 'EUR']
    stables = ['USDT']

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
        symbol = None
        if "/" in market:
            symbol = market.split("/")[0]
        else:
            logger.warning(f"no quote currency found for {market}")
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
        print(quote)
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

    def get_position(self, market: str):
        """Get the size of a spot, fiat, stable or future position

        Args:
            market (str): The symbol such as 'USD', 'USDT', 'BTC/USD' or 'BTC-PERP'

        Returns:
            [float]: The amount of asset held in the account
        """
        balances, type = None, None
        market = market.upper()
        symbol = market

        if any(currency == market for currency in self.fiats + self.stables):  # stable and fiat
            type = 'stable'
            balances = self.client.get_balances()
            positions = list(filter(lambda x: x['coin'] == symbol, balances))
        elif any(fiat in market for fiat in self.fiats):  # spot
            type = 'coin'
            balances = self.client.get_balances()
            symbol = self._parse_symbol(market)
            positions = list(filter(lambda x: x['coin'] == symbol, balances))
        else:  # futures
            type = 'future'
            balances = self.client.get_positions()
            positions = list(filter(lambda x: x['future'] == symbol, balances))

        if len(positions) == 1:
            if type == 'coin' or type == 'stable':
                retval = positions.pop().get("total")
            else:
                retval = positions.pop().get("size")
            logger.info(f"{market} has exactly one open {type} position of size {retval}")
            return retval
        elif not len(positions):
            logger.info(f"{market} does not have an open position")
            return 0.0
        else:
            raise IndexError(f"more than one position for {market} {type} in {positions}")

    def execute_chase_orderbook(self, tp_qs):
        """Executes a QuerySet of TargetPosition by aggressively chasing
        the top of the order book.

        Args:
            tp_qs (QuerySet): A list of TargetPosition
        """

        markets = [position.security for position in tp_qs]
        logger.info("starting execution...")
        logger.info(markets)
        pass

    def set_position(self, market: str, target_position: float):
        """[summary]

        Args:
            market ([type]): [description]
            target_position ([type]): [description]
        """

        # TODO Need to consider if you can enter a short position on this security.
        current_position = self.get_position(market)

        delta = target_position - current_position

        if delta < 0:
            delta = abs(delta)
            self._place_order(market, self.SELL, delta)
        else:
            self._place_order(market, self.BUY, delta)

        # TODO
        # log whatgever you do.

    def _get_price_from_orderbook(self, market, bids_asks: str, depth: int):
        """Get price at nth level in the orderbook

        Args:
            market (str): The market symbol
            bids_asks (str): If we're interested in bids or asks
            depth (int): Distance to the top of the orderbook
        """
        if bids_asks == 'bids' or bids_asks == 'asks':
            order_book = self.client.get_orderbook(market=market, depth=depth)
            return order_book[bids_asks][-1][0]
        else:
            raise AssertionError(f"bids_asks should be either asks or bids and not {bids_asks}")

    def _place_order(self, market: str, side: str, units: float):
        """[summary]

        Args:
            market ([type]): [description]
            side ([type]): [description]
            units ([type]): [description]
        """

        ### TODO Also need to check open orders....

        # target_price = self.get_target_price(market, side)
        bids_asks = 'bids' if side == 'buy' else 'asks'
        target_price = self._get_price_from_orderbook(market=market, bids_asks=bids_asks, depth=10)
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
            logger.info(f"{market} order size {units} is less than the tick size {tick}")
            return {'id': 000000000000, 'status': 'testing'}

        # if we're shorting an asset an it's spot we need to make sure it's available for borrow
        # CRO is an example of an asset that is in the universe and can't be borrowed - therefore need future
        # TODO ideally this needs to be handled by Security model Manager
        if side == self.SELL:
            # get lending rate, if it returns empty list then probably it's a future so we can carry on
            lending_rates = self.client.get_market_info(market)
            if lending_rates:
                symbol = self._parse_symbol(market)
                rate = next(rate for rate in lending_rates if rate["coin"] == symbol)
                if rate['estimatedRate'] == None:
                    logger.warning(f"Cannot open a short spot position for {market}, not available for borrow.")
                    return {'id': 000000000000, 'status': 'failed'}

        if self.testmode == False or 'LTC' in market:
            try:
                order_response = self.client.place_order(
                    market=str(market),
                    side=side,
                    price=target_price,
                    size=units,
                    type="limit",
                    post_only=True,
                )
                logger.info(json.dumps(order_response))
                return order_response

            except Exception as e:
                print("Exception!!")
                raise e
        # return JSON for testing mode
        else:
            return {'id': 000000000000, 'status': 'testing'}
