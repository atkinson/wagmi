import logging
import math

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
        # TODO check there is one and only one result?
        return self.client.get_market(market=market)

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
        offset = math.ceil(spread_in_ticks / 2)

        if (side == self.BUY) and ((bid + offset) < ask):
            return bid + offset
        elif side == self.BUY:
            return bid
        elif (side == self.SELL) and ((ask - offset) > bid):
            return ask - offset
        else:
            return ask

    def get_tick_size(self, market):
        quote = self.get_quote(market)
        return quote.get("sizeIncrement")

    def get_position(self, market: str):
        """[summary]

        Args:
            market ([type]): [description]

        Returns:
            [type]: [description]
        """
        spot_balances = self.client.get_balances()  # spot
        positions = list(filter(lambda x: x["coin"] == market, spot_balances))
        if len(positions) == 1:
            return positions.pop().get("total")
        elif not len(positions):
            return 0.0
        else:
            raise IndexError(
                f"more than one position for {market} in {positions}"
            )

    def set_position(self, market: str, target_position: float):
        """[summary]

        Args:
            market ([type]): [description]
            target_position ([type]): [description]
        """

        # TODO This is currently opening positions when there's already a position.
        current_position = self.get_position(market)

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
            print(
                f"{market} order size {units} is less than the tick size {tick}"
            )

        elif self.testmode == False:
            try:
                print(
                    self.client.place_order(
                        market=str(market),
                        side=side,
                        price=target_price,
                        size=units,
                        type="limit",
                    )
                )
            except Exception as e:
                print("Exception!!")
                raise e
