import json
import logging
import os
import sys

from efbl.document import eFBLDocument


logger = logging.getLogger()
logger.setLevel(logging.INFO)
stream_handler = logging.StreamHandler(sys.stdout)
logger.addHandler(stream_handler)


if __name__ == "__main__":
    document_api = eFBLDocument()
    assert document_api.health() is True

    with open("test_payload.json", "r") as payload_file:
        payload = payload_file.read()
        to_replace = {"FREIGHT_FORWARDER_ID": os.getenv("FREIGHT_FORWARDER_ID")}
        for key, value in to_replace.items():
            payload = payload.replace(key, value)
        json_payload = json.loads(payload)

    document_api.post_preview_document(json_payload)