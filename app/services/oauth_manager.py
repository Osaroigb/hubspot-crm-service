import time
import logging
import requests
from app.utils.errors import UnauthorizedError, ServiceUnavailableError

class OAuthManager:
    """
    Manages HubSpot OAuth token retrieval and refreshing.
    Stores the current access token in memory for simplicity.
    """

    HUBSPOT_TOKEN_URL="https://api.hubapi.com/oauth/v1/token"

    def __init__(self, client_id, client_secret, refresh_token):
        self.client_id = client_id
        self.client_secret = client_secret
        self.refresh_token = refresh_token

        self.access_token = None
        self.token_expires_at = 0  # Unix timestamp when token expires


    def get_access_token(self):
        """
        Retrieve a valid access token, refreshing if necessary.
        """
        current_time = time.time()

        if not self.access_token or current_time >= self.token_expires_at:
            logging.info("Access token is missing or expired. Refreshing...")
            self.refresh_access_token()

        return self.access_token


    def refresh_access_token(self):
        """
        Exchanges the refresh token for a new access token.
        Raises exceptions on failure.
        """
        payload = {
            "grant_type": "refresh_token",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "refresh_token": self.refresh_token
        }

        try:
            response = requests.post(self.HUBSPOT_TOKEN_URL, data=payload, timeout=10)
        except requests.exceptions.RequestException as e:
            logging.error(f"OAuth request exception: {e}")
            raise ServiceUnavailableError("Failed to reach HubSpot token endpoint.") from e

        if response.status_code != 200:
            logging.error(
                f"Failed to refresh access token. "
                f"Status: {response.status_code}, Body: {response.text}"
            )

            raise UnauthorizedError("Invalid or expired HubSpot refresh token.")

        data = response.json()
        self.access_token = data["access_token"]
        self.refresh_token = data.get("refresh_token", self.refresh_token)
        
        # Optional: Some responses do not contain a new refresh token. We keep the old one if missing.
        expires_in = data.get("expires_in", 1800)  # Default 30 minutes if not given
        self.token_expires_at = time.time() + expires_in - 60  # Refresh 1 minute early

        logging.info(f"Successfully refreshed HubSpot access token.")