import pytest
from django.test import TestCase
from django.core import management
from sizing.models import Strategy, StrategyPositionRequest, TargetPosition, Order
from .test_server import TestServer

strategy_under_test = "yolo"
strategy_url = "http://localhost:8000/weights/yolo"
weights_payload = """{
  "data": [
    {
      "arrival_price": 4526.6,
      "combo_weight": 0.0671891499550644,
      "date": "2021-11-25",
      "momentum_megafactor": 0.11640211640211642,
      "ticker": "ETH/USD",
      "trend_megafactor": 0.017976183508012392
    },
    {
      "arrival_price": 58982.0,
      "combo_weight": -0.0011975625714371416,
      "date": "2021-11-25",
      "momentum_megafactor": 0.021164021164021166,
      "ticker": "BTC/USD",
      "trend_megafactor": -0.02355914630689545
    }
  ],
  "last_updated": 1637885346,
  "success": "true"
}
"""


class Test(TestCase):
    def setUp(self) -> None:
        management.call_command(
            "loaddata", "sizing/fixtures/exchanges.yaml", verbosity=0
        )
        management.call_command(
            "loaddata", "sizing/fixtures/strategies.yaml", verbosity=0
        )
        strategy = Strategy.objects.get(name="yolo")
        strategy.url = strategy_url
        strategy.execute_immediately = False
        strategy.save()

        self.test_server = TestServer()
        self.test_server.run(weights_payload)
        pass

    def tearDown(self) -> None:
        self.test_server.stop()
        pass

    @pytest.mark.django_db
    def test_yolo(self) -> None:
        command = "rw_yolo"
        management.call_command(command)
        sprs_results = StrategyPositionRequest.objects.all()
        sprs_text = [str(spr) for spr in sprs_results]
        self.assertEqual(
            sprs_text[0],
            '{"strategy": "yolo", "exchange": "ftx", "security": "ETH/USD", "weight": 0.0671891499550644, "arrival_price_usd": 4526.6}',
        )
        self.assertEqual(
            sprs_text[1],
            '{"strategy": "yolo", "exchange": "ftx", "security": "BTC/USD", "weight": -0.0011975625714371416, "arrival_price_usd": 58982.0}',
        )

        tp_results = TargetPosition.objects.all()
        tp_text = [str(tp) for tp in tp_results]
        self.assertEqual(
            tp_text[0],
            '{"security": "ETH/USD", "exchange": "ftx", "size": 0.014843182511170503}',
        )
        self.assertEqual(
            tp_text[1],
            '{"security": "BTC/USD", "exchange": "ftx", "size": -2.0303865101847033e-05}',
        )
        pass
