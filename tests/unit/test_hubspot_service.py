import pytest
from marshmallow import ValidationError
from unittest.mock import patch, MagicMock
from app.services.hubspot_service import HubSpotService
from app.utils.errors import UnprocessableEntityError, NotFoundError


@pytest.fixture
def service():
    """
    Provide a HubSpotService instance with a mock hubspot_api dependency.
    This ensures we're only testing the service logic, not real API calls.
    """
    mock_hubspot_api = MagicMock()
    return HubSpotService(hubspot_api=mock_hubspot_api)


# ----------------- CONTACT TESTS ------------------ #

def test_create_or_update_contact_creates_new_contact(service):
    """
    If find_contact_by_email returns None, the service should call create_contact.
    """
    # Arrange: mock the internal method find_contact_by_email to return None
    with patch.object(service, 'find_contact_by_email', return_value=None):
        with patch.object(service, 'create_contact', return_value={"id": "123", "properties": {}}) as mock_create:
            
            # Act: call create_or_update_contact with valid data
            data = {
                "email": "johndoe@example.com",
                "firstname": "John",
                "lastname": "Doe",
                "phone": "+123456789"
            }

            result, action = service.create_or_update_contact(data)
            mock_create.assert_called_once()

            assert result == {"id": "123", "properties": {}}
            assert action == "created"


def test_create_or_update_contact_updates_existing_contact(service):
    """
    If find_contact_by_email returns an ID, the service should call update_contact.
    """
    with patch.object(service, 'find_contact_by_email', return_value="abc-123"):
        with patch.object(service, 'update_contact', return_value={"id": "abc-123", "properties": {"email": "johndoe@example.com"}}) as mock_update:
            data = {
                "email": "johndoe@example.com",
                "firstname": "John",
                "lastname": "Doe",
                "phone": "+123456789"
            }


            result, action = service.create_or_update_contact(data)
            mock_update.assert_called_once()

            assert result["id"] == "abc-123"
            assert result["properties"]["email"] == "johndoe@example.com"
            assert action == "updated"


def test_create_or_update_contact_invalid_data(service):
    """
    If required fields are missing, create_or_update_contact should raise UnprocessableEntityError.
    """
    # Missing 'email'
    invalid_data = {
        "firstname": "John",
        "lastname": "Doe",
        "phone": "+123456789"
    }

    # We expect marshmallow ValidationError inside the service => UnprocessableEntityError
    with pytest.raises(UnprocessableEntityError) as exc_info:
        service.create_or_update_contact(invalid_data)

    # Optionally assert the error message
    assert "Invalid contact data." in str(exc_info.value)


# ----------------- DEAL TESTS ------------------ #

def test_create_or_update_deals_creates_and_updates_deals(service):
    contact_id = "1234"
    deals_payload = [
        {
            "dealname": "New Website Build",
            "amount": 5000.00,
            "dealstage": "qualifiedtobuy"
        },
        {
            "dealname": "New Website Build",  # duplicate deal, will update instead
            "amount": 6000.00,
            "dealstage": "presentation"
        }
    ]

    with patch.object(service, 'assert_contact_exists') as mock_assert_contact_exists, \
         patch.object(service.deal_schema, 'load', side_effect=lambda d: d) as mock_validate, \
         patch.object(service, 'find_deal_by_name', side_effect=[None, "abc-789"]) as mock_find, \
         patch.object(service, 'create_deal', return_value={"id": "deal-1", "properties": {"dealname": "New Website Build"}}) as mock_create, \
         patch.object(service, 'update_deal', return_value={"id": "deal-2", "properties": {"dealname": "New Website Build"}}) as mock_update, \
         patch.object(service, 'associate_deal_with_contact') as mock_associate:

        results = service.create_or_update_deals(contact_id, deals_payload)

        assert mock_assert_contact_exists.called
        assert len(results) == 2

        created_result, updated_result = results

        # First was created
        assert created_result[1] == "created"
        assert created_result[0]["id"] == "deal-1"

        # Second was updated
        assert updated_result[1] == "updated"
        assert updated_result[0]["id"] == "deal-2"

        mock_create.assert_called_once()
        mock_update.assert_called_once()
        assert mock_associate.call_count == 2


def test_create_or_update_deals_invalid_deal_data(service):
    contact_id = "1234"
    invalid_deal_payload = [{
        "dealname": "",  # Missing required fields or invalid
        "amount": "not_a_number",
        "dealstage": ""
    }]

    with patch.object(service, 'assert_contact_exists'), \
         patch.object(service.deal_schema, 'load', side_effect=ValidationError("Invalid data")):
        
        with pytest.raises(UnprocessableEntityError) as exc_info:
            service.create_or_update_deals(contact_id, invalid_deal_payload)
        
        assert exc_info.value.message == "Invalid deal data"
        assert "Invalid data" in str(exc_info.value.verboseMessage)


def test_create_or_update_deals_raises_if_contact_not_found(service):
    contact_id = "invalid-contact"
    deals_payload = [
        {
            "dealname": "Something",
            "amount": 100.0,
            "dealstage": "qualifiedtobuy"
        }
    ]

    with patch.object(service, 'assert_contact_exists', side_effect=NotFoundError("Contact not found")):
        with pytest.raises(NotFoundError) as exc_info:
            service.create_or_update_deals(contact_id, deals_payload)
        
        assert "Contact not found" in str(exc_info.value)


# ----------------- TICKET TESTS ------------------ #

def test_create_tickets_success(service):
    contact_id = "1234"
    tickets_data = [
        {
            "subject": "Billing Issue - Payment Not Processed",
            "description": "The user was charged but didn't get confirmation.",
            "category": "billing",
            "pipeline": "support_pipeline_1",
            "hs_ticket_priority": "HIGH",
            "hs_pipeline_stage": "1"
        }
    ]

    mock_ticket = {"id": "ticket-1", "properties": {"subject": "Billing Issue - Payment Not Processed"}}

    with patch.object(service, 'assert_contact_exists'), \
         patch.object(service.ticket_schema, 'load', side_effect=lambda d: d) as mock_validate, \
         patch.object(service, 'fetch_associated_deals_for_contact', return_value=([], [])) as mock_fetch_deals, \
         patch.object(service, 'create_ticket', return_value=mock_ticket) as mock_create_ticket, \
         patch.object(service, 'associate_ticket_with_contact') as mock_assoc_contact, \
         patch.object(service, 'associate_ticket_with_deal') as mock_assoc_deal:

        result = service.create_tickets(contact_id, tickets_data)

        assert len(result) == 1
        ticket, action = result[0]

        assert action == "created"
        assert ticket["id"] == "ticket-1"
        
        mock_create_ticket.assert_called_once()
        mock_assoc_contact.assert_called_once()
        mock_assoc_deal.assert_not_called()


def test_create_tickets_with_deals(service):
    contact_id = "1234"
    tickets_data = [
        {
            "subject": "Technical Glitch",
            "description": "App crashes when uploading files.",
            "category": "technical_issue",
            "pipeline": "support_pipeline_1",
            "hs_ticket_priority": "MEDIUM",
            "hs_pipeline_stage": "1"
        }
    ]

    deal_ids = ["deal-1", "deal-2"]
    mock_ticket = {"id": "ticket-2", "properties": {"subject": "Technical Glitch"}}

    with patch.object(service, 'assert_contact_exists'), \
         patch.object(service.ticket_schema, 'load', side_effect=lambda d: d), \
         patch.object(service, 'fetch_associated_deals_for_contact', return_value=([{"id": i} for i in deal_ids], deal_ids)), \
         patch.object(service, 'create_ticket', return_value=mock_ticket), \
         patch.object(service, 'associate_ticket_with_contact') as mock_assoc_contact, \
         patch.object(service, 'associate_ticket_with_deal') as mock_assoc_deal:

        result = service.create_tickets(contact_id, tickets_data)

        assert result[0][0]["id"] == "ticket-2"
        assert result[0][1] == "created"
        assert mock_assoc_contact.call_count == 1
        assert mock_assoc_deal.call_count == len(deal_ids)


def test_create_tickets_invalid_ticket_data(service):
    contact_id = "1234"
    invalid_ticket_data = [
        {
            "subject": "",  # Missing mandatory fields
            "description": "",
            "category": "invalid",
            "pipeline": "",
            "hs_ticket_priority": "",
            "hs_pipeline_stage": ""
        }
    ]

    with patch.object(service, 'assert_contact_exists'), \
         patch.object(service.ticket_schema, 'load', side_effect=ValidationError("Invalid ticket fields")):

        with pytest.raises(UnprocessableEntityError) as exc_info:
            service.create_tickets(contact_id, invalid_ticket_data)

        assert exc_info.value.message == "Invalid ticket data"
        assert "Invalid ticket fields" in str(exc_info.value.verboseMessage)


def test_create_tickets_contact_not_found(service):
    contact_id = "invalid-contact"
    tickets_data = [
        {
            "subject": "Glitch",
            "description": "Crash",
            "category": "technical_issue",
            "pipeline": "support_pipeline_1",
            "hs_ticket_priority": "HIGH",
            "hs_pipeline_stage": "1"
        }
    ]

    with patch.object(service, 'assert_contact_exists', side_effect=NotFoundError("Contact not found")):

        with pytest.raises(NotFoundError) as exc_info:
            service.create_tickets(contact_id, tickets_data)

        assert "Contact not found" in str(exc_info.value)