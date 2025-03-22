import time
import pytest
import requests
from unittest.mock import patch, MagicMock
from app.services.oauth_manager import OAuthManager
from app.utils.errors import UnauthorizedError, ServiceUnavailableError


@pytest.fixture
def oauth_manager():
    return OAuthManager(
        client_id="dummy-client-id",
        client_secret="dummy-client-secret",
        refresh_token="dummy-refresh-token"
    )


def test_get_access_token_uses_cached_token(oauth_manager):
    oauth_manager.access_token = "cached-token"
    oauth_manager.token_expires_at = time.time() + 300  # valid for 5 more minutes

    with patch.object(oauth_manager, 'refresh_access_token') as mock_refresh:
        token = oauth_manager.get_access_token()
        assert token == "cached-token"
        mock_refresh.assert_not_called()


def test_get_access_token_triggers_refresh(oauth_manager):
    oauth_manager.access_token = None
    oauth_manager.token_expires_at = 0

    with patch.object(oauth_manager, 'refresh_access_token') as mock_refresh:
        mock_refresh.return_value = None
        oauth_manager.access_token = "new-token"

        token = oauth_manager.get_access_token()
        assert token == "new-token"
        mock_refresh.assert_called_once()


def test_refresh_access_token_success(oauth_manager):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "access_token": "new-access-token",
        "expires_in": 3600
    }

    with patch("requests.post", return_value=mock_response):
        oauth_manager.refresh_access_token()

        assert oauth_manager.access_token == "new-access-token"
        assert oauth_manager.token_expires_at > time.time()


def test_refresh_access_token_failure_status(oauth_manager):
    mock_response = MagicMock()
    mock_response.status_code = 401
    mock_response.text = "Unauthorized"

    with patch("requests.post", return_value=mock_response):
        with pytest.raises(UnauthorizedError) as exc:
            oauth_manager.refresh_access_token()
        assert "Invalid or expired" in str(exc.value)


def test_refresh_access_token_network_error(oauth_manager):
    with patch("requests.post", side_effect=requests.exceptions.ConnectionError):
        with pytest.raises(ServiceUnavailableError) as exc:
            oauth_manager.refresh_access_token()
        assert "Failed to reach HubSpot" in str(exc.value)


def test_refresh_token_updated_if_provided(oauth_manager):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "access_token": "access-123",
        "refresh_token": "refresh-456",
        "expires_in": 1800
    }

    with patch("requests.post", return_value=mock_response):
        oauth_manager.refresh_access_token()
        assert oauth_manager.refresh_token == "refresh-456"


def test_refresh_token_remains_if_not_provided(oauth_manager):
    old_refresh_token = oauth_manager.refresh_token
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "access_token": "access-999",
        "expires_in": 1800
    }

    with patch("requests.post", return_value=mock_response):
        oauth_manager.refresh_access_token()
        assert oauth_manager.refresh_token == old_refresh_token