import json
import logging
import os
import sys
import time
from typing import IO

from efbl.document import eFBLDocument


logger = logging.getLogger()
logger.setLevel(logging.INFO)
stream_handler = logging.StreamHandler(sys.stdout)
logger.addHandler(stream_handler)


def is_pdf(filelike: IO[bytes]) -> bool:
    try:
        header = filelike.read(5)
        return header == b"%PDF-"
    except Exception as e:
        logger.error(f"Can't read file: {e}")
        return False


if __name__ == "__main__":
    document_api = eFBLDocument()
    assert document_api.health() is True

    with open("test_payload.json") as payload_file:
        payload = payload_file.read()
        to_replace = {"FREIGHT_FORWARDER_ID": os.getenv("FREIGHT_FORWARDER_ID")}
        for key, value in to_replace.items():
            payload = payload.replace(key, value)
        json_payload = json.loads(payload)

    preview_pdf = document_api.post_preview_document(json_payload)
    assert is_pdf(preview_pdf)

    document_id, issued_pdf = document_api.post_issuance_document(json_payload)
    assert is_pdf(issued_pdf)
    assert len(document_id) == 17
    attempts = 0
    while attempts < 5:
        verification_data = document_api.verify_document(document_id)
        if verification_data.get("registered") is True:
            logger.info("Document verified")
            break
        else:
            # it might take a while for the document to be verifiable
            time.sleep(1)  # wait 5 seconds before trying again
        attempts += 1
    assert attempts != 5, "Document was not verified"
