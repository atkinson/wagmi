import logging
from django.conf import settings
from django.db import models
from django.db.models.deletion import CASCADE
from execution.exchanges import ftx
from django.utils import timezone

logger = logging.getLogger("execution")


class AuditableMixin(object):

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class OrderManager(models.Manager):
    def create_order(self, target_position):

        if target_position.exchange.name == "ftx":
            logger.debug("Using exchange ftx")
            exchange = ftx.FTXExchange(
                subaccount=settings.WAGMI_FTX_SUB_ACCOUNT,
                testmode=settings.WAGMI_ORDER_TESTMODE,
                api_key=settings.WAGMI_FTX_API_KEY,
                api_secret=settings.WAGMI_FTX_API_SECRET,
            )
            exchange.set_position(
                market=target_position.security.name,
                target_position=target_position.size,
            )

    def create_orders(self, qs):
        """Receives a queryset of TargetPositions.
        Get's current position from exchange.
        Post's order to correct position"""
        for target_position in qs:
            self.create_order(target_position)


class Order(models.Model, AuditableMixin):

    # Having these here causes circular dependency, what's the best solution?
    security = models.ForeignKey("sizing.Security", on_delete=models.CASCADE)
    exchange = models.ForeignKey("sizing.Exchange", on_delete=models.CASCADE)
    size = models.FloatField(help_text="how many units of the security")

    # created_at = models.DateTimeField(auto_now_add=True)

    objects = OrderManager()


class Fill(models.Model, AuditableMixin):
    # order = models.ForeignKey("Order", on_delete=models.CASCADE)

    # int
    id = models.IntegerField(primary_key=True, editable=False)

    # boolean
    ioc = models.BooleanField(default=None, editable=False)
    postOnly = models.BooleanField(default=None, editable=False)
    reduceOnly = models.BooleanField(default=None, editable=False)
    liquidation = models.BooleanField(default=None, editable=False)

    # float
    size = models.FloatField(default=None, editable=False)
    price = models.FloatField(default=None, editable=False)
    filledSize = models.FloatField(default=None, editable=False)
    avgFillPrice = models.FloatField(default=None, editable=False)
    remainingSize = models.FloatField(default=None, editable=False)

    # char
    market = models.CharField(default=None, editable=False, max_length=10)
    side = models.CharField(default=None, editable=False, max_length=4)
    type = models.CharField(default=None, editable=False, max_length=5)
    status = models.CharField(default=None, editable=False, max_length=10)
    clientId = models.CharField(default=None, editable=False, max_length=10)

    # datetime
    createdAt = models.DateTimeField(default=timezone.now, editable=False)
