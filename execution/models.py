import logging

from django.conf import settings
from django.db import models
from django.utils import timezone

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
            Order.objects.create(security=target_position.security,
                                 exchange=target_position.exchange,
                                 size=target_position.size)

    def chase_execute(self, tpr_qs):
        """Receives a queryset of TargetPositions.
        Gets current position from exchange.
        Post's order to correct position"""

        exchange = ftx.FTXExchange(
            subaccount=settings.WAGMI_FTX_SUB_ACCOUNT,
            testmode=settings.WAGMI_ORDER_TESTMODE,
            api_key=settings.WAGMI_FTX_API_KEY,
            api_secret=settings.WAGMI_FTX_API_SECRET,
        )
        orders = []
        # compute delta, place the order and add to the database
        for sp in tpr_qs:
            position = exchange.get_position(sp.security.name)
            delta = position - sp.size
            side = 'buy' if delta > 0 else 'sell'

            order = Order.objects.create(security=sp.security,
                                         exchange=sp.exchange,
                                         side=side,
                                         size=sp.size,
                                         size_delta=delta,
                                         )

            response = exchange._place_order(market=sp.security.name,
                                             side=side,
                                             units=abs(delta))

            order.order_id = response['id']
            order.status = response['status']
            order.save()
            orders.append(order)

        # TODO loops through orders and update price until they're all filled


class Order(models.Model, AuditableMixin):
    security = models.ForeignKey("sizing.Security", on_delete=models.CASCADE)
    exchange = models.ForeignKey("sizing.Exchange", on_delete=models.CASCADE)
    size = models.FloatField(help_text="how many units of the security")
    size_delta = models.FloatField()

    created_at = models.DateTimeField(auto_now_add=True)

    order_id = models.BigIntegerField(default=0)

    status = models.CharField(default='created', max_length=10)
    side = models.CharField(default=None, editable=False, max_length=10)

    objects = OrderManager()


class FillManager(models.Manager):

    def create_from_ftx(self, fills):
        for fill in fills:
            Fill.objects.create(**fill)


class Fill(models.Model, AuditableMixin):
    """ Variable names match those of FTX,
    so you can easily submit fills using
    Fill(**order_response)

    https://docs.ftx.com/#fills
    """

    # order = models.ForeignKey("Order", on_delete=models.CASCADE)

    # int
    # FTX has 12 integer index, so need Big BigIntegerField (which I think is faster than CharField)
    id = models.BigIntegerField(primary_key=True, editable=False, db_index=True)
    orderId = models.BigIntegerField(editable=False)
    tradeId = models.BigIntegerField(editable=False)

    # float
    fee = models.FloatField(default=None, editable=False)
    feeRate = models.FloatField(default=None, editable=False)
    price = models.FloatField(default=None, editable=False)
    size = models.FloatField(default=None, editable=False)

    # char
    feeCurrency = models.CharField(default=None, editable=False, max_length=10)
    future = models.CharField(default=None, editable=False, max_length=20, null=True)
    liquidity = models.CharField(default=None, editable=False, max_length=10)
    market = models.CharField(default=None, editable=False, max_length=20)
    baseCurrency = models.CharField(default=None, editable=False, max_length=10, null=True)
    quoteCurrency = models.CharField(default=None, editable=False, max_length=10, null=True)
    side = models.CharField(default=None, editable=False, max_length=10)
    type = models.CharField(default=None, editable=False, max_length=10)

    # datetime
    time = models.DateTimeField(default=timezone.now, editable=False)
    recorded_at = models.DateTimeField(auto_now_add=True, editable=False)

    objects = FillManager()
