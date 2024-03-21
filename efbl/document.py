import os
import logging

import requests

from .auth import get_token


API_SERVER = os.getenv("API_SERVER")
CLIENT_ID = os.getenv("CLIENT_ID")
SOFTWARE_PROVIDER_ID = os.getenv("SOFTWARE_PROVIDER_ID")

DOCUMENT_ISSUANCE_ENDPOINT = f"{API_SERVER}/api/trakk/v0/integrations/fiata/fbl-json"
HEALTH_ENDPOINT = f"{API_SERVER}/api/trakk/v0/integrations/health"
PREVIEW_MODE = "preview"
ISSUANCE_MODE = "issuance"
AMENDMENT_MODE = "amendment"


logger = logging.getLogger(__name__)


class eFBLDocument:
    def __init__(self):
        self.token = get_token()

    def _get_request(self, url, params=None, payload=None):
        if params is None:
            params = {}
        if payload is None:
            verb = "GET"
        else:
            verb = "POST"
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
            "X-Alias-ID": CLIENT_ID
        }
        return requests.request(verb, url, headers=headers, params=params, json=payload)

    def health(self):
        response = self._get_request(HEALTH_ENDPOINT)
        if response.status_code != 204:
            logger.error("Health check failed")
            return False
        logger.info("Health check successful")
        return True

    def post_preview_document(self, payload):
        url_params = {"softwareProviderId": SOFTWARE_PROVIDER_ID, "mode": PREVIEW_MODE}
        response = self._get_request(DOCUMENT_ISSUANCE_ENDPOINT, params=url_params, payload=payload)
        if response.status_code != 200:
            logger.error(f"Failed to post preview document: {response.text}")
            return False
        logger.info("Preview document posted successfully")
        return True
