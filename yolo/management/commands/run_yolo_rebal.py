# runapscheduler.py
import logging

from django.conf import settings
from django.core.management.base import BaseCommand

from yolo.runner import get_yolo_weights

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Runs YOLO"

    def handle(self, *args, **options):
        get_yolo_weights()
