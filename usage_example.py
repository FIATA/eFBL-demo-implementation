import argparse
import json
import logging
import os
import sys
import time
from datetime import datetime
from typing import IO

from efbl.document import eFBLDocument


logger = logging.getLogger()
logger.setLevel(logging.INFO)
stream_handler = logging.StreamHandler(sys.stdout)
logger.addHandler(stream_handler)


def is_pdf(filelike: IO[bytes]) -> bool:
    try:
        header = filelike.read(5)
        filelike.seek(0)
        return header == b"%PDF-"
    except Exception as e:
        logger.error(f"Can't read file: {e}")
        return False


def save_pdf(filelike: IO[bytes], folder: str, label: str) -> None:
    """Save a PDF file with a timestamp in the specified folder.

    Args:
        filelike: A file-like object containing PDF content.
        folder: The destination folder to save the PDF.
        label: A string label to include in the filename.
    """
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    filename = f"{label}_{timestamp}.pdf"
    path = os.path.join(folder, filename)
    with open(path, "wb") as f:
        f.write(filelike.read())
    filelike.seek(0)
    logger.info(f"Saved PDF: {path}")


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments.

    Returns:
        The parsed argument namespace.
    """
    parser = argparse.ArgumentParser(description="Generate and optionally save eFBL documents.")
    parser.add_argument(
        "--save", metavar="FOLDER", help="Folder where PDFs should be saved with timestamped filenames"
    )
    return parser.parse_args()


def prepare_payload(filepath: str) -> dict:
    """Load and prepare the payload with environment substitution.

    Args:
        filepath: Path to the JSON payload file.

    Returns:
        A parsed and modified payload dictionary.
    """
    with open(filepath) as f:
        raw = f.read()
    freight_id = os.getenv("FREIGHT_FORWARDER_ID")
    if not freight_id:
        raise OSError("FREIGHT_FORWARDER_ID environment variable is not set.")
    return json.loads(raw.replace("FREIGHT_FORWARDER_ID", freight_id))


def verify_document(document_api: eFBLDocument, document_id: str, max_attempts: int = 5) -> None:
    """Poll the API until the document is verified or max attempts reached.

    Args:
        document_api: The eFBLDocument API instance.
        document_id: The ID of the document to verify.
        max_attempts: Maximum number of verification attempts.
    """
    for _attempt in range(max_attempts):
        verification_data = document_api.verify_document(document_id)
        if verification_data.get("registered") is True:
            logger.info("Document verified")
            return
        time.sleep(1.5)
    raise RuntimeError("Document was not verified")


def main() -> None:
    args = parse_args()
    if args.save:
        if not os.path.isdir(args.save):
            logger.error(f"Save folder does not exist: {args.save}")
            sys.exit(1)

    document_api = eFBLDocument()
    assert document_api.health() is True

    payload = prepare_payload("test_payload.json")

    preview_pdf = document_api.post_preview_document(payload)
    assert is_pdf(preview_pdf)
    if args.save:
        save_pdf(preview_pdf, args.save, "preview")

    document_id, issued_pdf = document_api.post_issuance_document(payload)
    assert is_pdf(issued_pdf)
    assert len(document_id) == 17
    if args.save:
        save_pdf(issued_pdf, args.save, "issuance")
    verify_document(document_api, document_id)

    amended_payload = payload.copy()
    amended_payload["exchanged_document"]["id"] = document_id
    amended_payload["supply_chain_consignment"]["consignor"]["name"]["value"] = "Amended Consignor"
    amended_document_id, amended_pdf = document_api.post_amendment_document(amended_payload)
    assert amended_document_id == document_id
    assert is_pdf(amended_pdf)
    if args.save:
        save_pdf(amended_pdf, args.save, "amendment")

    verify_document(document_api, document_id)


if __name__ == "__main__":
    main()
