import json

from django.http.response import HttpResponse
from django.views import View
from django.conf import settings

from google.cloud import secretmanager


def gcp_get_secret(project_id, secret_id):
    """
    Access the payload for the given secret version if one exists. The version
    can be a version number as a string (e.g. "5") or an alias (e.g. "latest").
    """
    # Create the Secret Manager client.
    client = secretmanager.SecretManagerServiceClient()

    # Build the resource name of the secret version.
    name = f"projects/{project_id}/secrets/{secret_id}/versions/latest"

    # Access the secret version.
    response = client.access_secret_version(request={"name": name})

    return json.loads(response.payload.data.decode("UTF-8"))


class GCPPubSubHandlerBaseView(View):
    def dispatch(self, request, *args, **kwargs):
        envelope = json.loads(request.body.decode("utf-8"))

        if not envelope:
            msg = "no Pub/Sub message received"
            print(f"error: {msg}")
            return HttpResponse(f"Bad Request: {msg}", status=400)

        if not isinstance(envelope, dict) or "message" not in envelope:
            msg = "invalid Pub/Sub message format"
            print(f"error: {msg}")
            return HttpResponse(f"Bad Request: {msg}", status=400)

        return super().dispatch(request, *args, **kwargs)
