import os, base64, json

from django.http import JsonResponse
from django.http.response import HttpResponse
from django.views import View
from django.conf import settings

from helpers.gcptools import GCPPubSubHandlerBaseView
from .ftx_execution import FTXExecute

DEBUG = settings.DEBUG


def gcp_get_secret():
    with open("/secrets/ftx_momo") as jsonFile:
        jsonObj = json.load(jsonFile)
        jsonFile.close()
    return jsonObj


class ExecuteTrade(GCPPubSubHandlerBaseView):
    def post(self, request, *args, **kwargs):
        pubsub_message = json.loads(request.body.decode("utf-8")).get(
            "message"
        )

        if isinstance(pubsub_message, dict) and "data" in pubsub_message:
            payload = json.loads(
                base64.b64decode(pubsub_message["data"])
                .decode("utf-8")
                .strip()
            )
            if payload["market"] and payload["sized_usd"]:
                apikey = gcp_get_secret()
                executor = FTXExecute(
                    subaccount=payload["subaccount"],
                    debug=DEBUG,
                    api_key=apikey["key"],
                    api_secret=apikey["secret"],
                )
            # this thing needs context.
            if payload["side"] == -1:
                print(
                    f"received signal: {payload['market']} {payload['side']}"
                )
                executor.take_side(
                    executor.SHORT, payload["market"], payload["sized_usd"]
                )
            elif payload["side"] == 1:
                print(
                    f"received signal: {payload['market']} {payload['side']}"
                )
                executor.take_side(
                    executor.LONG, payload["market"], payload["sized_usd"]
                )
            else:
                print(
                    f"received signal: {payload['market']} {payload['side']}"
                )
                executor.close_position(payload["market"])
            return HttpResponse("OK", status=202)
        else:
            return HttpResponse("not enough information to trade", status=400)


# from django.core.cache import cache

# # Create your views here.
# # cache.set('my_key', 'hello, world!', 30)
# # cache.get('my_key')
