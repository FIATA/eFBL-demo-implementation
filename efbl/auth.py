import os

from dotenv import load_dotenv
import requests


load_dotenv()  # Load environment variables from .env file

AUTH_SERVER = os.getenv("AUTH_SERVER")
AUTH_URL_PATTERN = f"{AUTH_SERVER}/auth/realms/fiata/protocol/openid-connect/token"
GRANT_TYPE = "password"


def get_token():
    """
    Get a token from the Keycloak server.

    Returns:
        str: The token.
    """
    response = requests.post(
        AUTH_URL_PATTERN,
        data={
            "username": os.getenv("USERNAME"),
            "password": os.getenv("PASSWORD"),
            "client_id": os.getenv("CLIENT_ID"),
            "client_secret": os.getenv("FREIGHT_FORWARDER_ID"),
            "grant_type": GRANT_TYPE,
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    return response.json()["access_token"]

