import logging
import json
from django.db import models
from django.conf import settings
from datetime import datetime
from django.utils import timezone

logger = logging.getLogger("sizing")


class Strategy(models.Model):

    name = models.CharField(max_length=24, db_index=True)
    exchange = models.ForeignKey("Exchange", on_delete=models.CASCADE)
    max_position_size_usd = models.DecimalField(
        max_digits=9,
        decimal_places=2,
        help_text="Maximum position size in USD. A Strategy should weight it's investments as a proportion of this size.",
        default=1000.0,
    )
    url = models.URLField("endpoint url")
    execute_immediately = models.BooleanField(default=False)
    command = models.CharField(max_length=24)

    class Meta:
        verbose_name_plural = "Strategies"

    def __str__(self):
        return self.name


class Exchange(models.Model):

    name = models.CharField(max_length=24, db_index=True)

    class Meta:
        verbose_name_plural = "Exchanges"

    def __str__(self):
        return self.name


class Security(models.Model):

    name = models.CharField(max_length=24, db_index=True)

    class Meta:
        verbose_name_plural = "Securities"

    def __str__(self):
        return self.name


class StrategyPositionRequestManager(models.Manager):
    def set_position(
        self,
        strategy_name: str,
        exchange_name: str,
        security_name: str,
        weight: float,
        arrival_price_usd: float,
        calculated_at: datetime,
    ):
        strategy, _ = Strategy.objects.get_or_create(name=strategy_name)
        exchange, _ = Exchange.objects.get_or_create(name=exchange_name)
        security, _ = Security.objects.get_or_create(name=security_name)

        obj, created = StrategyPositionRequest.objects.update_or_create(
            strategy=strategy,
            exchange=exchange,
            security=security,
            defaults={
                "weight": weight,
                "arrival_price_usd": arrival_price_usd,
                "calculated_at": calculated_at,
            },
        )
        return obj

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
        weight (float): Notional weight of the request (not shares or dollars)
        arrival_price_usd (float): Price in USd of the security when we calculated weights
        calculated_at (datetime): Datetime when the weisghts were calculated.
    """

    strategy = models.ForeignKey("Strategy", on_delete=models.CASCADE)
    exchange = models.ForeignKey("Exchange", on_delete=models.CASCADE)
    security = models.ForeignKey("Security", on_delete=models.CASCADE)
    weight = models.FloatField()
    arrival_price_usd = models.FloatField()
    calculated_at = models.DateTimeField()

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
    def create_new_desired_positions(
        self, security=None, execute_immediately=False
    ):
        """Once all new Position Requests are in for the day,
        we can now calculate the net of all of these as a set
        of TargetPositions. One TargetPosition per Security.

        Optional - pass in a Security, or Queryset of Security models.
        """
        if (
            security
            and isinstance(security, models.QuerySet)
            and security.model is Security
        ):
            securities = security
        elif security and isinstance(security, Security):
            securities = Security.objects.filter(id=security.id)
        elif security:
            raise TypeError(
                "security should be a single Security or a queryset, or None"
            )
        else:
            securities = Security.objects.all()

        for security in securities:
            desired_size = 0.0

            spr_qs = StrategyPositionRequest.objects.filter(security=security)

            for req in spr_qs:
                desired_size += req.weight * float(
                    req.strategy.max_position_size_usd
                )

            tp, created = TargetPosition.objects.update_or_create(
                security=security,
                exchange=req.exchange,  # TODO - do we care about multiple exchanges?
                defaults={"size": desired_size / req.arrival_price_usd},
            )
            if execute_immediately:
                from execution.models import Order

                Order.objects.create_order(tp)

            for req in spr_qs:
                logger.info(
                    f"TargetPosition {tp.id} includes StrategyPositionRequest {req.strategy}, {req.exchange}, {req.security}, {req.weight}, {req.arrival_price_usd}"
                )


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
    updated_at = models.DateTimeField(auto_now=True)

    objects = TargetPositionManager()

    def __str__(self):
        return f"[{self.exchange.name}] {self.security.name} = {self.size}"
