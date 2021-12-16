import logging
from datetime import datetime

from django.utils import timezone

import requests
from django.conf import settings

from sizing.models import Strategy, StrategyPositionRequest, TargetPosition

strategy = Strategy.objects.get(name="yolo")

logger = logging.getLogger(strategy.name)

url = f"{strategy.url}?api_key={settings.RW_API_KEY}"


def get_yolo_weights():
    """Call the API, get the weights, send for sizing."""
    resp = requests.get(url=url)
    yolo = resp.json()

    if yolo.get("success") == "true":
        last_updated = yolo.get("last_updated")
        data = yolo.get("data")

        # we normalise the weights such that their absolute sum is 1 to allocate all max_position_size_usd
        abs_sum_weights = sum([abs(weight['combo_weight']) for weight in data])

        for position in data:
            logger.info(
                f"{position.get('ticker')}, {position.get('combo_weight')}, {position.get('arrival_price')}"
            )
            calculated_at = datetime.fromtimestamp(last_updated, timezone.utc)

            # TODO check if calculated_at is more recent than those currently stored in DB

            spr = StrategyPositionRequest.objects.set_position(
                strategy_name=strategy.name,
                exchange_name=strategy.exchange,
                security_name=position.get("ticker"),
                weight=position.get("combo_weight"),
                norm_weight=position.get("combo_weight") / abs_sum_weights,
                arrival_price_usd=position.get("arrival_price"),
                calculated_at=calculated_at,
            )

            TargetPosition.objects.create_new_desired_positions(
                security=spr.security,
                execute_immediately=strategy.execute_immediately,
            )

        closing_positions = StrategyPositionRequest.objects.filter(
            strategy=strategy, calculated_at__lt=calculated_at
        )
        closing_positions.update(weight=0.0)
        for position in closing_positions:
            TargetPosition.objects.create_new_desired_positions(
                security=position.security,
                execute_immediately=position.execute_immediately,
            )

        # Only once we've created all TargetPosition's, we send them for batch execution
        TargetPosition.objects.processTargetPosition()

    else:
        logger.error(f'yolo api failed: {yolo.get("message")}\nURL:{url}')
