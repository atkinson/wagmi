import ftx

class FTXExecute(object):

    BUY = LONG = "buy"
    SELL = SHORT = "sell"

    def __init__(self, subaccount, debug, api_key, api_secret) -> None:

        self.client = ftx.FtxClient(
            api_key=api_key, api_secret=api_secret, subaccount_name=subaccount
        )
        self.debug = debug
        print(f"Executor inited with debug={debug}")

    def place_order(self, market, side, size_usd):
        latest = self.client.get_future(market)

        if side == self.BUY:
            limit = latest["ask"]  # * 0.9995
        else:
            limit = latest["bid"]  # * 1.0005

        size = size_usd / limit

        print(
            'endpoint="executor",'
            "debug={}, "
            'market="{}", '
            'side="{}", '
            "price={:,.4f}, "
            "size={:,.4f}".format(self.debug, market, side, limit, size)
        )

        if not self.debug:
            try:
                self.client.place_order(
                    market=market,
                    side=side,
                    price=limit,
                    size=size,
                    type="limit",
                )
            except Exception as e:
                print(e)

    def take_side(self, side, market, size_usd):
        position = self.client.get_position(market)
        latest = self.client.get_future(market)

        if (position is None) or (position["size"] == 0):
            print(f"OPEN {side} for: {market}")
            self.place_order(market, side, size_usd)

        elif (
            (position["side"] == self.SHORT)
            and (side == self.LONG)
            and position["size"] > 0.0
        ):
            # need to buy to cover plus take long position
            print(f"LONG to SHORT switch for : {market}")
            approx_order = (position["size"] * latest["ask"]) + size_usd
            self.place_order(market, self.LONG, approx_order)

        elif (
            (position["side"] == self.LONG)
            and (side == self.SHORT)
            and position["size"] > 0.0
        ):
            # need to sell to close plus take short position
            print(f"SHORT to LONG switch for : {market}")
            approx_order = (position["size"] * latest["bid"]) + size_usd
            self.place_order(market, self.SHORT, approx_order)
        else:
            print(f"Did not trade {market}")

    def close_position(self, market):
        position = self.client.get_position(market)
        latest = self.client.get_future(market)

        if position["side"] == self.SHORT:
            desired_side = self.LONG
        else:
            desired_side = self.SHORT

        if desired_side == self.LONG:
            limit = latest["ask"]  # * 0.9995
        else:
            limit = latest["bid"]  # * 1.0005

        print(
            "debug={}, "
            'market="{}", '
            'side="{}", '
            "price={:,.4f}, "
            "size={:,.4f}".format(
                self.debug,
                position["future"],
                desired_side,
                limit,
                position["size"],
            )
        )

        if not self.debug:
            try:
                self.client.place_order(
                    market=position["future"],
                    side=desired_side,
                    price=limit,
                    size=position["size"],
                    type="limit",
                    reduce_only=True,
                )
            except Exception as e:
                print(e)

    def close_all_positions(self):
        """
        While closing the position, I want to be more agressive
        to get out before the reversion kicks in.
        """
        for position in self.client.get_positions():
            if position["size"] != 0.0:
                self.close_position(position["future"])

        print("Closed all positions.")
