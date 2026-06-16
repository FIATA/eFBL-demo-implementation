import argparse
import json
import logging
import os
import sys
import time
from collections.abc import Iterable
from datetime import datetime
from typing import IO

from efbl.cli_output import StateColorFormatter
from efbl.document import eFBLDocument


logger = logging.getLogger()
logger.setLevel(logging.INFO)
stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setFormatter(StateColorFormatter())
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


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments.

    Returns:
        The parsed argument namespace.
    """
    parser = argparse.ArgumentParser(description="Generate and optionally save eFBL documents.")
    parser.add_argument(
        "payload",
        help=("Path to JSON payload file(s). Use '-' to read a single payload from stdin."),
    )
    parser.add_argument(
        "--save", metavar="FOLDER", help="Folder where PDFs should be saved with timestamped filenames"
    )
    parser.add_argument(
        "--no-verify",
        dest="verify",
        action="store_false",
        help="Do not poll the API to verify documents after issuance",
    )
    parser.add_argument(
        "--attempts",
        type=int,
        default=5,
        help="Number of verification attempts (default: 5)",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=1.5,
        help="Seconds to sleep between verification attempts (default: 1.5)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable debug logging",
    )
    return parser.parse_args(list(argv) if argv is not None else None)


def prepare_payload_from_file(path: str) -> dict:
    """
    Load a JSON payload from path or stdin and substitute environment vars.
    Supports reading from '-' to load JSON from stdin. Substitutes the token
    "FREIGHT_FORWARDER_ID" in the raw JSON with the environment variable
    FREIGHT_FORWARDER_ID. Raises OSError when the env var is missing.
    Args:
    path: File path or '-' for stdin.
    Returns:
    Parsed JSON payload as a dict.
    """
    if path == "-":
        raw = sys.stdin.read()
    else:
        with open(path, encoding="utf-8") as fh:
            raw = fh.read()
    freight_id = os.getenv("FREIGHT_FORWARDER_ID")
    if not freight_id:
        raise OSError("FREIGHT_FORWARDER_ID environment variable is not set.")
    substituted = raw.replace("FREIGHT_FORWARDER_ID", freight_id)
    return json.loads(substituted)


def verify_document(document_api: eFBLDocument, document_id: str, max_attempts: int = 5, timeout: float = 1.5) -> None:
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
        time.sleep(timeout)
    raise RuntimeError("Document was not verified")


def process_payload(
    document_api: eFBLDocument, payload: dict, save_folder: str | None, verify: bool, attempts: int, timeout: float
) -> None:
    """Process a single payload: preview, issuance, amendment and optional save/verify.
    Args:
    document_api: eFBLDocument API instance.
    payload: Parsed JSON payload dictionary.
    save_folder: Optional folder to save generated PDFs.
    verify: Whether to perform verification polling.
    attempts: Max verification attempts.
    timeout: Seconds between verification attempts.
    """
    preview_pdf = document_api.post_preview_document(payload)
    assert is_pdf(preview_pdf)
    if save_folder:
        save_pdf(preview_pdf, save_folder, "preview")

    document_id, issued_pdf = document_api.post_issuance_document(payload)
    assert is_pdf(issued_pdf)
    if not isinstance(document_id, str) or len(document_id) == 0:
        raise RuntimeError("Invalid document id returned from issuance")
    if save_folder:
        save_pdf(issued_pdf, save_folder, "issuance")

    if verify:
        verify_document(document_api, document_id, max_attempts=attempts, timeout=timeout)

    # create an amended payload as example
    amended_payload = payload.copy()
    amended_payload["exchanged_document"]["id"] = document_id
    # be defensive: only change if keys exist
    try:
        amended_payload["supply_chain_consignment"]["consignor"]["name"]["value"] = "Amended Consignor"
    except Exception:  # pragma: no cover - best-effort amendment
        logger.debug("Could not set amended consignor name; payload structure differs")

    amended_document_id, amended_pdf = document_api.post_amendment_document(amended_payload)
    assert amended_document_id == document_id
    assert is_pdf(amended_pdf)
    if save_folder:
        save_pdf(amended_pdf, save_folder, "amendment")

    if verify:
        verify_document(document_api, document_id, max_attempts=attempts, timeout=timeout)


def main() -> None:
    args = parse_args()
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    if args.save and not os.path.isdir(args.save):
        logger.error("Save folder does not exist: %s", args.save)
        sys.exit(1)

    document_api = eFBLDocument()
    assert document_api.health() is True

    payload_path = args.payload
    logger.info("Processing payload: %s", payload_path)
    try:
        payload = prepare_payload_from_file(payload_path)
    except Exception as exc:
        logger.exception("Failed to prepare payload %s: %s", payload_path, exc)
        sys.exit(1)

    try:
        process_payload(
            document_api,
            payload,
            save_folder=args.save,
            verify=args.verify,
            attempts=args.attempts,
            timeout=args.timeout,
        )
    except Exception:
        logger.exception("Processing payload %s failed", payload_path)
    sys.exit(1)


if __name__ == "__main__":
    main()
