import pytest
import json
from .ftx import FTXExchange


class TestFTXExchange:
    @pytest.mark.parametrize(
        "side,expected,test_input",
        [
            (
                "buy",
                49483,
                '{"bid": 49483.0, "ask": 49484.0, "priceIncrement": 1.0, "sizeIncrement": 0.0001, "price": 49484.0}',
            ),
            (
                "buy",
                49482,
                '{"bid": 49480.0, "ask": 49484.0, "priceIncrement": 1.0, "sizeIncrement": 0.0001, "price": 49484.0}',
            ),
            (
                "sell",
                49484,
                '{"bid": 49483.0, "ask": 49484.0, "priceIncrement": 1.0, "sizeIncrement": 0.0001, "price": 49484.0}',
            ),
            (
                "sell",
                49482,
                '{"bid": 49480.0, "ask": 49484.0, "priceIncrement": 1.0, "sizeIncrement": 0.0001, "price": 49484.0}',
            ),
        ],
    )
    def test__get_spread_midpoint(self, side, expected, test_input) -> None:
        ftx = FTXExchange(
            subaccount="pytest", testmode=True, api_key="none", api_secret="none"
        )
        quote = json.loads(test_input)
        assert expected == ftx._get_spread_midpoint(quote, side)

    def test__get_spread_midpoint_unknownside(self) -> None:
        ftx = FTXExchange(
            subaccount="pytest", testmode=True, api_key="none", api_secret="none"
        )
        quote = json.loads(
            '{"bid": 49483.0, "ask": 49484.0, "priceIncrement": 1.0, "sizeIncrement": 0.0001, "price": 49484.0}'
        )
        with pytest.raises(NotImplementedError, match="Unsupported side: sellshort"):
            ftx._get_spread_midpoint(quote, "sellshort")
