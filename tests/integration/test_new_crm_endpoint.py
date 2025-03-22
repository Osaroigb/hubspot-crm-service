from unittest.mock import patch

CRM_OBJECTS_URL = "/api/v1/hubspot/new-crm-objects"

def test_missing_since_param(client):
    response = client.get(CRM_OBJECTS_URL)
    data = response.get_json()

    assert response.status_code == 400
    assert data["success"] is False
    assert "since" in data["error_message"].lower()


@patch("app.services.hubspot_service.HubSpotService.retrieve_new_crm_objects")
def test_success_retrieve_new_crm_objects(mock_retrieve, client):
    mock_response = {
        "contacts": [
            {"id": "1", "properties": {"email": "new@example.com"}, "associatedDeals": []}
        ],
        "contacts_paging": None,
        "deals": [],
        "deals_paging": None,
        "tickets": [],
        "tickets_paging": None
    }

    mock_retrieve.return_value = mock_response

    response = client.get(CRM_OBJECTS_URL + "?since=2025-03-20T00:00:00Z")
    data = response.get_json()

    assert response.status_code == 200
    assert data["success"] is True
    assert "contacts" in data["data"]


@patch("app.services.hubspot_service.HubSpotService.retrieve_new_crm_objects")
def test_internal_error_on_retrieve(mock_retrieve, client):
    mock_retrieve.side_effect = Exception("HubSpot exploded")

    response = client.get(CRM_OBJECTS_URL + "?since=2025-03-20T00:00:00Z")
    data = response.get_json()

    assert response.status_code == 500
    assert data["success"] is False
    assert "hubspot exploded" in data["data"].lower()


@patch("app.services.hubspot_service.HubSpotService.retrieve_new_crm_objects")
def test_with_pagination_and_limit(mock_retrieve, client):
    mock_retrieve.return_value = {
        "contacts": [],
        "contacts_paging": {"next": {"after": "4"}},
        "deals": [],
        "deals_paging": None,
        "tickets": [],
        "tickets_paging": None
    }

    response = client.get(CRM_OBJECTS_URL + "?since=2025-03-20T00:00:00Z&limit=5&after=2")
    data = response.get_json()

    assert response.status_code == 200
    assert data["success"] is True
    assert data["data"]["contacts_paging"]["next"]["after"] == "4"
