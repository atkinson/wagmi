import logging
import json
from decimal import Decimal
from django.db import models
from django.conf import settings

logger = logging.getLogger("sizing")


class Strategy(models.Model):

    name = models.CharField(max_length=24, db_index=True)
    exchange = models.ForeignKey("Exchange", on_delete=models.CASCADE)
    max_position_size_usd = models.DecimalField(
        max_digits=9,
        decimal_places=2,
        help_text="Maximum position size in USD. A Strategy may hold many positions of this size.",
        default=1000.0,
    )
    command = models.CharField(max_length=24)

    def __str__(self):
        return self.name


class Exchange(models.Model):

    name = models.CharField(max_length=24, db_index=True)

    def __str__(self):
        return self.name


class Security(models.Model):

    name = models.CharField(max_length=24, db_index=True)

    def __str__(self):
        return self.name


class StrategyPositionRequestManager(models.Manager):
    def open(
        self,
        strategy_name: str,
        exchange_name: str,
        security_name: str,
        weight: float,
        arrival_price_usd: float,
    ):
        strategy, _ = Strategy.objects.get_or_create(name=strategy_name)
        exchange, _ = Exchange.objects.get_or_create(name=exchange_name)
        security, _ = Security.objects.get_or_create(name=security_name)

        return StrategyPositionRequest.objects.create(
            strategy=strategy,
            exchange=exchange,
            security=security,
            weight=weight,
            arrival_price_usd=arrival_price_usd,
        )

    def close(
        self, strategy_name: str, exchange_name: str, security_name: str
    ):
        position = self.get_position(
            strategy_name, exchange_name, security_name
        )

        strategy, _ = Strategy.objects.get_or_create(name=strategy_name)
        exchange, _ = Exchange.objects.get_or_create(name=exchange_name)
        security, _ = Security.objects.get_or_create(name=security_name)

        StrategyPositionRequest.objects.create(
            strategy=strategy,
            exchange=exchange,
            security=security,
            size=-position,
        )

    def get_position(
        self, strategy_name: str, exchange_name: str, security_name: str
    ):
        return StrategyPositionRequest.objects.filter(
            strategy__name=strategy_name,
            exchange__name=exchange_name,
            security__name=security_name,
        ).aggregate(models.Sum("size"))["size__sum"]


class StrategyPositionRequest(models.Model):
    """A Strategy can request a position in a Security on an Exchange.

    Fields:
        strategy (Strategy): The Strategy making this request
        exchange (Exchange): Exchange the security should be traded on
        security (Security): The security to be traded
        size (float): Notional size in units of the request (not shares or dollars)
    """

    strategy = models.ForeignKey("Strategy", on_delete=models.CASCADE)
    exchange = models.ForeignKey("Exchange", on_delete=models.CASCADE)
    security = models.ForeignKey("Security", on_delete=models.CASCADE)
    weight = models.FloatField()
    arrival_price_usd = models.FloatField()

    desired_position = models.ForeignKey(
        "TargetPosition",
        null=True,
        related_name="position_requests",
        on_delete=models.SET_NULL,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = StrategyPositionRequestManager()

    def __str__(self):
        return json.dumps(
            {
                "strategy": self.strategy.name,
                "exchange": self.exchange.name,
                "security": self.security.name,
                "weight": self.weight,
                "arrival_price_usd": self.arrival_price_usd,
            }
        )


class TargetPositionManager(models.Manager):
    def create_new_desired_positions(self, security=None):
        """Once all new Position Requests are in for the day,
        we can now calculate the net of all of these as a set
        of TargetPositions. One TargetPosition per Security.

        Optional - pass in a Security to only recalaculate that one.
        """
        if security:
            securities = Security.objects.filter(id=security.id)
        else:
            securities = Security.objects.all()

        for security in securities:

            desired_size = Decimal(0.0)

            reqs = StrategyPositionRequest.objects.filter(
                security=security, desired_position=None
            )

            for req in reqs:
                desired_size += (
                    Decimal(req.weight) * req.strategy.max_position_size_usd
                )

            dp = TargetPosition.objects.create(
                security=security,
                exchange=req.exchange,  # TODO - do we care about multiple exchanges?
                size=desired_size / Decimal(req.arrival_price_usd),
            )

            for req in reqs:
                logger.info(
                    f"TargetPosition {dp.id} includes StrategyPositionRequest {req.strategy}, {req.exchange}, {req.security}, {req.weight}, {req.arrival_price_usd}"
                )
                req.delete()


class TargetPosition(models.Model):
    """Every Security needs a desired position.

    The aggregate of all strategies.

    Fields:
        security ([type]): The security to be traded
        exchange ([type]): Exchange the security should be traded on
        size ([type]): Size in tradeable units (e.g. shares).
    """

    security = models.ForeignKey("Security", on_delete=models.CASCADE)
    exchange = models.ForeignKey("Exchange", on_delete=models.CASCADE)
    size = models.FloatField(help_text="how many units of the security")

    created_at = models.DateTimeField(auto_now_add=True)

    objects = TargetPositionManager()
