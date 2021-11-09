import logging
from datetime import datetime

from django.utils import timezone

import requests
from django.conf import settings

from sizing.models import Strategy, StrategyPositionRequest, TargetPosition

strategy = Strategy.objects.get(name="yolo")

logger = logging.getLogger(strategy.name)

url = f"https://api.robotwealth.com/v1/yolo/weights?api_key={settings.RW_YOLO_API_KEY}"


def get_yolo_weights():
    """Call the API, get the weights, send for sizing."""
    resp = requests.get(url=url)
    yolo = resp.json()

    if yolo.get("success") == "true":
        for position in yolo.get("data"):
            logger.info(
                f"{position.get('ticker')}, {position.get('combo_weight')}, {position.get('arrival_price')}"
            )
            calculated_at = timezone.make_aware(
                datetime.strptime(position.get("date"), "%Y-%m-%d"),
                timezone.utc,
            )

            StrategyPositionRequest.objects.set_position(
                strategy_name=strategy.name,
                exchange_name=strategy.exchange,
                security_name=position.get("ticker"),
                weight=position.get("combo_weight"),
                arrival_price_usd=position.get("arrival_price"),
                calculated_at=calculated_at,
            )

        StrategyPositionRequest.objects.filter(
            strategy=strategy, calculated_at__lt=calculated_at
        ).update(weight=0.0)

        TargetPosition.objects.create_new_desired_positions()
    else:
        logger.error(f'yolo api failed: {yolo.get("message")}')
