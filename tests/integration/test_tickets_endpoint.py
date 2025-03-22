import json
import pytest
from unittest.mock import patch

TICKETS_URL = "/api/v1/hubspot/tickets"

@pytest.fixture
def valid_ticket_payload():
    return {
        "contactId": "1234",
        "tickets": [
            {
                "subject": "Website Issue",
                "description": "Page not loading properly",
                "category": "technical_issue",
                "pipeline": "support_pipeline_1",
                "hs_ticket_priority": "HIGH",
                "hs_pipeline_stage": "1"
            }
        ]
    }


def test_create_tickets_success(client, valid_ticket_payload):
    with patch("app.services.hubspot_service.HubSpotService.create_tickets") as mock_create:
        mock_create.return_value = [
            ({"id": "123456", "properties": valid_ticket_payload["tickets"][0]}, "created")
        ]

        response = client.post(TICKETS_URL, data=json.dumps(valid_ticket_payload), content_type="application/json")
        data = response.get_json()

        assert response.status_code == 200
        assert data["success"] is True
        assert data["message"] == "Tickets created successfully."
        assert data["data"][0]["action"] == "created"


def test_create_tickets_missing_contact_id(client, valid_ticket_payload):
    payload = valid_ticket_payload.copy()
    payload.pop("contactId")

    response = client.post(TICKETS_URL, data=json.dumps(payload), content_type="application/json")
    data = response.get_json()

    assert response.status_code == 400
    assert data["success"] is False
    assert "contactId is required" in data["error_message"]


def test_create_tickets_empty_tickets_list(client):
    payload = {
        "contactId": "1234",
        "tickets": []
    }

    response = client.post(TICKETS_URL, data=json.dumps(payload), content_type="application/json")
    data = response.get_json()

    assert response.status_code == 400
    assert data["success"] is False
    assert "At least one ticket object is required" in data["error_message"]


def test_create_tickets_internal_server_error(client, valid_ticket_payload):
    with patch("app.services.hubspot_service.HubSpotService.create_tickets") as mock_create:
        mock_create.side_effect = Exception("HubSpot service crashed")

        response = client.post(TICKETS_URL, data=json.dumps(valid_ticket_payload), content_type="application/json")
        data = response.get_json()

        assert response.status_code == 500
        assert data["success"] is False
        assert "hubspot service crashed" in str(data["data"]).lower()