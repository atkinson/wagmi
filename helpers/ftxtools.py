from datetime import datetime, timedelta, timezone
from tinydb import TinyDB, Query

import ftx

import pandas as pd


class FTXObject:
    def __init__(self, token):
        for key in token:
            setattr(self, key, token[key])


class LeveragedToken(FTXObject):
    def calc_pending_rebalance(self):
        """
        When a rebalance is triggered (currently 00:02 UTC),
        FTX calculates the number of units of the underlying the
        LT needs to buy/sell to return to 3x leverage, marked to
        prices at that time.
        """
        desired_position = (
            float(self.leverage) * self.totalNav / self.underlyingMark
        )

        current_position = self.positionPerShare * self.outstanding

        return desired_position - current_position


class Future(FTXObject):
    def __init__(self, *args, **kwargs):
        self._lt_list = None
        super(Future, self).__init__(*args, **kwargs)

    @property
    def hourly_volume(self):
        return self.volume / 24

    @property
    def hourly_volume_usd(self):
        return self.volumeUsd24h / 24

    @property
    def lt_list(self):
        return self._lt_list

    def set_lt_list(self, lt_list):
        self._lt_list = lt_list

    @property
    def market_impact(self):
        """
        Basic metric for market impact of the rebalance.
        """
        return self.rebal_size / self.hourly_volume

    @property
    def pending_rebal_usd(self):
        return self.rebal_size * self.mark

    @property
    def rebal_size(self):
        pending_rebalance = 0.0
        for lt in self.lt_list:
            pending_rebalance += lt.calc_pending_rebalance()
        return pending_rebalance


class FTXStrategy:

    BUY = LONG = "buy"
    SELL = SHORT = "sell"

    MIN_HOURLY_VOLUME = 0

    perps = list()
    futures = list()
    leveraged_tokens = list()

    def __init__(
        self, subaccount, debug=False, api_key=None, api_secret=None
    ) -> None:

        self.client = ftx.FtxClient(
            api_key=api_key, api_secret=api_secret, subaccount_name=subaccount
        )

        for token in self.client.list_lts():
            lt = LeveragedToken(token)
            self.leveraged_tokens.append(lt)

        for future in self.client.get_futures():
            lt_list = [
                lt
                for lt in self.leveraged_tokens
                if lt.underlying == future["name"]
            ]

            f = Future(future)
            f.set_lt_list(lt_list)
            self.futures.append(f)

        self.perps = [future for future in self.futures if future.perpetual]

        self.debug = debug
        self.db = TinyDB("db.json")
        self.db.truncate()

    def place_order(self, market, side, size_usd):
        latest = self.client.get_future(market)

        if side == self.BUY:
            limit = latest["ask"]  # * 0.9995
        else:
            limit = latest["bid"]  # * 1.0005

        size = size_usd / limit

        print(
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

    def close_position(self, position):
        latest = self.client.get_future(position["future"])

        if position["side"] == self.SHORT:
            desired_side = self.BUY
        else:
            desired_side = self.SELL

        if desired_side == self.BUY:
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
                self.close_position(position)

        print("Closed all positions.")

    def pandl(self):

        start_time = (
            datetime.now(tz=timezone.utc) - timedelta(days=self.BACKTEST_DAYS)
        ).timestamp()
        end_time = (datetime.now(tz=timezone.utc)).timestamp()

        fills = pd.DataFrame(
            self.client.get_fills(start_time=start_time, end_time=end_time)
        )
        fills["time"] = pd.to_datetime(fills["time"])
        fills = fills.drop(["future", "baseCurrency", "quoteCurrency"], axis=1)
        fills = fills.sort_values(by="time", ascending=True)
        print(fills.tail(100))

        for idx, fill in fills.iterrows():
            # is this a new trade or an open one?
            Trade = Query()
            open_trades = self.db.search(
                (Trade.closed == False) & (Trade.market == fill["market"])
            )

            # if new, create a new row
            if len(open_trades) == 0:
                self.db.insert(
                    {
                        "id": fill["id"],
                        "time": fill["time"].isoformat(),
                        "market": fill["market"],
                        "side": fill["side"],
                        "size": fill["size"],
                        "size_now": fill["size"],
                        "total_fees": fill["fee"],
                        "consideration": fill["price"] * fill["size"],
                        "closed": False,
                        "net_profit": 0.0,
                    }
                )

            else:
                trade = open_trades[0]

                # if we're accumulating into the trade
                if fill["side"] == trade["side"]:

                    if (trade["size_now"] + fill["size"]) >= trade["size"]:
                        max_size = trade["size_now"] + fill["size"]
                    else:
                        max_size = trade["size"]

                    self.db.update(
                        {
                            "size_now": round(
                                trade["size_now"] + fill["size"], 4
                            ),
                            "size": max_size,
                            "total_fees": trade["total_fees"] + fill["fee"],
                            "consideration": trade["consideration"]
                            + (fill["price"] * fill["size"]),
                        },
                        Trade.id == trade["id"],
                    )

                else:
                    # we're reducing out of the trade (we must close any trade that croses sides)
                    size_now = round(trade["size_now"] - fill["size"], 4)

                    if size_now >= 0.0:
                        self.db.update(
                            {
                                "size_now": size_now,
                                "total_fees": trade["total_fees"]
                                + fill["fee"],
                                "consideration": trade["consideration"]
                                - (fill["price"] * fill["size"]),
                            },
                            Trade.id == trade["id"],
                        )
                    else:
                        # trade has crossed sides. Let's close out the trade and create a new one
                        size_to_close = trade["size_now"]
                        new_size = fill["size"] - trade["size_now"]

                        self.db.update(
                            {
                                "size_now": 0.0,
                                "total_fees": trade["total_fees"]
                                + fill["fee"] * (size_to_close / fill["size"]),
                                "consideration": trade["consideration"]
                                - (fill["price"] * size_to_close),
                            },
                            Trade.id == trade["id"],
                        )

                        self.db.insert(
                            {
                                "id": fill["id"],
                                "time": fill["time"].isoformat(),
                                "market": fill["market"],
                                "side": fill["side"],
                                "size": new_size,
                                "size_now": new_size,
                                "total_fees": fill["fee"]
                                * (new_size / fill["size"]),
                                "consideration": (fill["price"] * new_size),
                                "closed": False,
                                "net_profit": 0.0,
                            }
                        )

                # and maybe this is the final reduction to size 0
                ClosableTrades = Query()
                for trade in self.db.search(
                    (ClosableTrades.closed == False) & (Trade.size_now == 0)
                ):

                    if trade["side"] == "buy":
                        net_profit = (
                            -trade["consideration"] - trade["total_fees"]
                        )
                    else:
                        net_profit = (
                            trade["consideration"] - trade["total_fees"]
                        )

                    self.db.update(
                        {
                            "closed": True,
                            "net_profit": round(net_profit, 2),
                            "consideration": 0.0,
                            "total_fees": round(trade["total_fees"], 2),
                            "size": round(trade["size"], 4),
                        },
                        Trade.id == trade["id"],
                    )

        for row in self.db.all():
            print(row)
