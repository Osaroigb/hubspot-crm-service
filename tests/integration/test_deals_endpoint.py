import json
import pytest
from unittest.mock import patch
from app.utils.errors import NotFoundError

DEALS_URL = "/api/v1/hubspot/deals"

@pytest.fixture
def sample_payload():
    return {
        "contactId": "contact-123",
        "deals": [
            {
                "dealname": "Website Revamp",
                "amount": 1200.00,
                "dealstage": "appointmentscheduled"
            }
        ]
    }


@patch("app.services.hubspot_service.HubSpotService.create_or_update_deals")
def test_create_deals_success(mock_create_deals, client, sample_payload):
    mock_create_deals.return_value = [
        ({"id": "deal-1", "properties": sample_payload["deals"][0]}, "created")
    ]

    response = client.post(DEALS_URL, data=json.dumps(sample_payload), content_type="application/json")
    data = response.get_json()

    assert response.status_code == 200
    assert data["success"] is True
    assert data["message"] == "Deals processed successfully."
    assert data["data"][0]["action"] == "created"
    assert "deal" in data["data"][0]


def test_create_deals_missing_contact_id(client, sample_payload):
    del sample_payload["contactId"]

    response = client.post(DEALS_URL, data=json.dumps(sample_payload), content_type="application/json")
    data = response.get_json()

    assert response.status_code == 400
    assert data["success"] is False
    assert "contactId is required" in data["error_message"]


def test_create_deals_empty_deals_list(client, sample_payload):
    sample_payload["deals"] = []

    response = client.post(DEALS_URL, data=json.dumps(sample_payload), content_type="application/json")
    data = response.get_json()

    assert response.status_code == 400
    assert data["success"] is False
    assert "At least one deal object" in data["error_message"]


@patch("app.services.hubspot_service.HubSpotService.create_or_update_deals")
def test_create_deals_invalid_contact(mock_create_deals, client, sample_payload):
    mock_create_deals.side_effect = NotFoundError("Contact not found.")

    response = client.post(DEALS_URL, data=json.dumps(sample_payload), content_type="application/json")
    data = response.get_json()

    assert response.status_code == 404
    assert "Contact not found" in data["error_message"]
    assert data["success"] is False


@patch("app.services.hubspot_service.HubSpotService.create_or_update_deals")
def test_create_deals_internal_error(mock_create_deals, client, sample_payload):
    mock_create_deals.side_effect = Exception("HubSpot service crashed")

    response = client.post(DEALS_URL, data=json.dumps(sample_payload), content_type="application/json")
    data = response.get_json()

    assert response.status_code == 500
    assert data["success"] is False
    
    assert isinstance(data["data"], str)
    assert "crashed" in data["data"].lower()