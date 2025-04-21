import os

import requests
from dotenv import load_dotenv


load_dotenv()  # Load environment variables from .env file

AUTH_SERVER = os.getenv("AUTH_SERVER")
AUTH_URL_PATH = "/auth/realms/fiata/protocol/openid-connect/token"
AUTH_URL_PATTERN = f"{AUTH_SERVER}/auth/realms/fiata/protocol/openid-connect/token"
GRANT_TYPE = "password"


def get_token(
    username: str = None,
    password: str = None,
    client_id: str = None,
    freight_forwarder_id: str = None,
    auth_domain: str = None,
) -> str:
    """
    Get a token from the Keycloak server.

    Returns:
        str: The token.
    """
    if not auth_domain:
        auth_domain = AUTH_SERVER
    auth_url = auth_domain + AUTH_URL_PATH
    if not username:
        username = os.getenv("USERNAME")
    if not password:
        password = os.getenv("PASSWORD")
    if not client_id:
        client_id = os.getenv("CLIENT_ID")
    if not freight_forwarder_id:
        freight_forwarder_id = os.getenv("FREIGHT_FORWARDER_ID")
    data = {
        "username": username,
        "password": password,
        "client_id": client_id,
        "client_secret": freight_forwarder_id,
        "grant_type": GRANT_TYPE,
    }
    response = requests.post(
        auth_url,
        data=data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    if "access_token" not in response.json():
        print(data)
        raise ValueError("Failed to get token: " + response.text)
    return response.json()["access_token"]
