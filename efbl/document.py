import logging
import os
import re
from io import BytesIO
from typing import IO

import requests

from .auth import get_token


API_SERVER = os.getenv("API_SERVER")
VERIFICATION_SERVER = os.getenv("VERIFICATION_SERVER")
CLIENT_ID = os.getenv("CLIENT_ID")
SOFTWARE_PROVIDER_ID = os.getenv("SOFTWARE_PROVIDER_ID")

DOCUMENT_ISSUANCE_ENDPOINT = f"{API_SERVER}/api/trakk/v0/integrations/fiata/fbl-json"
HEALTH_ENDPOINT = f"{API_SERVER}/api/trakk/v0/integrations/health"
VERIFY_ENDPOINT = f"{VERIFICATION_SERVER}/api/magic-link/v0/documents/fiata/gdti"
PREVIEW_MODE = "preview"
ISSUANCE_MODE = "issuance"
AMENDMENT_MODE = "amendment"


logger = logging.getLogger(__name__)


def extract_document_id_from_response(response: requests.Response) -> str:
    content_disposition = response.headers.get("Content-Disposition", "")
    if not content_disposition:
        raise ValueError("Content-Disposition header is missing")

    # Use regex to find the filename in the Content-Disposition header
    filename_match = re.search(r"filename=([^;]+)", content_disposition)
    if not filename_match:
        raise ValueError("Filename not found in Content-Disposition header")

    filename = filename_match.group(1).strip().strip('"')

    # Extract the part of the filename before .pdf
    document_id_match = re.match(r"(.*)\.pdf", filename)
    if not document_id_match:
        raise ValueError("Filename does not contain .pdf extension")

    return document_id_match.group(1)


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
            "X-Alias-ID": CLIENT_ID,
        }
        return requests.request(verb, url, headers=headers, params=params, json=payload)

    def health(self):
        response = self._get_request(HEALTH_ENDPOINT)
        if response.status_code != 204:
            logger.error("Health check failed")
            return False
        logger.info("Health check successful")
        return True

    def post_preview_document(self, payload) -> IO[bytes]:
        url_params = {"softwareProviderId": SOFTWARE_PROVIDER_ID, "mode": PREVIEW_MODE}
        response = self._get_request(DOCUMENT_ISSUANCE_ENDPOINT, params=url_params, payload=payload)
        if response.status_code != 200:
            raise Exception(f"Failed to post preview document: {response.text}")
        logger.info("Preview document posted successfully")
        return BytesIO(response.content)

    def post_issuance_document(self, payload) -> tuple[str, IO[bytes]]:
        url_params = {"softwareProviderId": SOFTWARE_PROVIDER_ID, "mode": ISSUANCE_MODE}
        response = self._get_request(DOCUMENT_ISSUANCE_ENDPOINT, params=url_params, payload=payload)
        if response.status_code != 200:
            logger.error(f"Failed to post issuance document: {response.text}")
        logger.info("Issuance document posted successfully")
        document_id = extract_document_id_from_response(response)

        return document_id, BytesIO(response.content)

    def verify_document(self, document_id: str):
        response = self._get_request(f"{VERIFY_ENDPOINT}/{document_id}")
        if response.status_code != 200:
            logger.error(f"Failed to post verify document: {response.text}")
        logger.info("Document verification ran successfully")
        return response.json()
