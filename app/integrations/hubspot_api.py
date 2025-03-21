import time
import logging
import requests
from app.utils.errors import BadRequestError, NotFoundError, ServiceUnavailableError

class HubSpotAPI:
    def __init__(self, oauth_manager):
        """
        :param oauth_manager: An instance of OAuthManager that provides access tokens.
        """
        self.oauth_manager = oauth_manager

    def request(self, method, endpoint, json_data=None, params=None, max_retries=3):
        """
        Make an HTTP request to HubSpot API with exponential backoff for rate limits.

        :param method: HTTP method (GET, POST, PATCH, etc.).
        :param endpoint: HubSpot API endpoint (e.g., "/crm/v3/objects/contacts").
        :param json_data: Optional JSON payload.
        :param params: Optional query params dictionary.
        :param max_retries: Number of retries before failing.
        :return: JSON response from HubSpot (dict).
        """
        url = f"https://api.hubapi.com{endpoint}"
        attempt = 0
        wait_time = 5

        while attempt < max_retries:
            access_token = self.oauth_manager.get_access_token()
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {access_token}"
            }

            try:
                response = requests.request(
                    method=method.upper(),
                    url=url,
                    headers=headers,
                    json=json_data,
                    params=params,
                    timeout=10
                )
            except requests.exceptions.RequestException as e:
                logging.error(f"Request error to HubSpot: {e}")
                raise ServiceUnavailableError("Failed to connect to HubSpot API.") from e

            # Handle common status codes
            if response.status_code == 200 or response.status_code == 201:
                return response.json()
            
            elif response.status_code == 401:
                # Token expired or invalid; force refresh and retry
                logging.warning("HubSpot responded with 401. Refreshing token and retrying...")
                self.oauth_manager.refresh_access_token()

            elif response.status_code == 429:
                # Rate limited, exponential backoff
                logging.warning(f"Rate-limited by HubSpot. Waiting {wait_time}s before retry...")
                time.sleep(wait_time)
                wait_time *= 2

            elif response.status_code == 404:
                logging.error(f"Not found error 404: {response.text}")
        
                raise NotFoundError(
                    message="Resource not found in HubSpot",
                    verboseMessage=response.text
                )

            elif 400 <= response.status_code < 500:
                # Client error, possibly contact not found or validation error
                logging.error(f"Client error {response.status_code}: {response.text}")
                
                try:
                    error_json = response.json()
                    # HubSpot typically has error info in "message" or "errors" array
                    hubspot_message = error_json.get("message") or "Client error from HubSpot"
                except Exception:
                    hubspot_message = response.text  # fallback if not JSON

                # For 400-level errors, raise BadRequestError
                raise BadRequestError(
                    message=hubspot_message
                )
            
            elif response.status_code >= 500:
                # Server error, possible temporary issue
                logging.warning(f"HubSpot server error {response.status_code}. Retrying...")
                time.sleep(wait_time)
                wait_time *= 2

            else:
                # Unexpected status code
                logging.error(
                    f"Unexpected HubSpot response. Code: {response.status_code}, Body: {response.text}"
                )
                raise ServiceUnavailableError("Unexpected HubSpot API response.")

            attempt += 1
        
        # If we exit the while loop, we've exhausted our retries
        raise ServiceUnavailableError(
            f"Exceeded max retries ({max_retries}) for HubSpot API request."
        )