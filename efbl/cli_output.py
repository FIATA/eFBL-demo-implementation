import logging
import shlex

import requests


BLUE = "\033[94m"
YELLOW = "\033[93m"
RESET = "\033[0m"
SEPARATOR = "*" * 70


def request_to_curl(request: requests.PreparedRequest) -> str:
    """Build a curl command equivalent to the given prepared request."""
    parts = ["curl", "-X", request.method]
    for header, value in request.headers.items():
        parts += ["-H", shlex.quote(f"{header}: {value}")]
    if request.body:
        body = request.body
        if isinstance(body, bytes):
            body = body.decode("utf-8", errors="replace")
        parts += ["-d", shlex.quote(body)]
    parts.append(shlex.quote(request.url))
    return " ".join(parts)


def log_curl(response: requests.Response) -> None:
    """Print, in blue and framed by separators, the curl command equivalent to the
    request that produced this response."""
    curl_cmd = request_to_curl(response.request)
    print(f"{BLUE}{SEPARATOR}\n{curl_cmd}\n{SEPARATOR}{RESET}")


def log_state(message: str) -> None:
    """Print a status/state message in yellow, visually distinct from curl output."""
    print(f"{YELLOW}{message}{RESET}")


class StateColorFormatter(logging.Formatter):
    """Logging formatter that renders log messages in yellow, so that status/state
    logs stay visually distinct from the blue curl-equivalent output."""

    def format(self, record: logging.LogRecord) -> str:
        message = super().format(record)
        return f"{YELLOW}{message}{RESET}"
