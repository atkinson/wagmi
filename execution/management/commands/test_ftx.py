import logging

from django.conf import settings
from django.core.management.base import BaseCommand

from execution.exchanges import ftx

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Runs ftx tests."

    def handle(self, *args, **options):
        exchange = ftx.FTXExchange(
            subaccount=settings.WAGMI_FTX_SUB_ACCOUNT,
            testmode=settings.WAGMI_ORDER_TESTMODE,
            api_key=settings.WAGMI_FTX_API_KEY,
            api_secret=settings.WAGMI_FTX_API_SECRET,
        )
        exchange.set_position(market="BTC/USD", units=0.0001)
