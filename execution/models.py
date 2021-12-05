import logging
from django.conf import settings
from django.db import models
from django.db.models.deletion import CASCADE
from execution.exchanges import ftx

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
    objects = OrderManager()


class Fill(models.Model, AuditableMixin):
    order = models.ForeignKey(Order, on_delete=CASCADE)
