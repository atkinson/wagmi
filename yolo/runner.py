import requests
from django.conf import settings

url = f"https://api.robotwealth.com/v1/yolo/weights?{settings.RW_YOLO_API_KEY}"


def get_yolo_weights():
    """Call the API, get the weights, send for sizing."""
    resp = requests.get(url=url)
    data = resp.json()

    # TODO parse the data
    # TODO submit StrategyPositionRequests to Sizing.
