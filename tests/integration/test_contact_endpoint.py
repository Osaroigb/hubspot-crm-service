import json
from unittest.mock import patch

CONTACT_URL = "/api/v1/hubspot/contact"

@patch("app.services.hubspot_service.HubSpotService.create_or_update_contact")
def test_create_contact_success(mock_create_contact, client):
    payload = {
        "email": "john@example.com",
        "firstname": "John",
        "lastname": "Doe",
        "phone": "+123456789"
    }

    mock_create_contact.return_value = (
        {"id": "12345", "properties": payload}, "created"
    )

    response = client.post(CONTACT_URL, data=json.dumps(payload), content_type="application/json")
    data = response.get_json()

    assert response.status_code in [200, 201]
    assert data["success"] is True
    assert "created successfully" in data["message"].lower()


@patch("app.services.hubspot_service.HubSpotService.create_or_update_contact")
def test_update_existing_contact_success(mock_create_contact, client):
    payload = {
        "email": "jane@example.com",
        "firstname": "Jane",
        "lastname": "Smith",
        "phone": "+447911111111"
    }

    mock_create_contact.return_value = (
        {"id": "999", "properties": payload}, "updated"
    )

    response = client.post(CONTACT_URL, data=json.dumps(payload), content_type="application/json")
    data = response.get_json()

    assert response.status_code == 200
    assert data["success"] is True
    assert "updated successfully" in data["message"].lower()


def test_missing_required_field(client):
    payload = {
        "email": "missing@name.com",
        "lastname": "Doe"
        # Missing firstname and phone
    }

    response = client.post(CONTACT_URL, data=json.dumps(payload), content_type="application/json")
    data = response.get_json()

    assert response.status_code == 422
    assert data["success"] is False
    assert "error_message" in data


@patch("app.services.hubspot_service.HubSpotService.create_or_update_contact")
def test_hubspot_internal_error(mock_create_contact, client):
    payload = {
        "email": "fail@example.com",
        "firstname": "Fail",
        "lastname": "Case",
        "phone": "+123456789"
    }

    mock_create_contact.side_effect = Exception("Simulated failure")

    response = client.post(CONTACT_URL, data=json.dumps(payload), content_type="application/json")
    data = response.get_json()

    assert response.status_code == 500
    assert data["success"] is False
    assert "simulated failure" in data.get("data", "").lower()