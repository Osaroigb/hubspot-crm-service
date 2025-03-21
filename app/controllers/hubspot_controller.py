from flask import Blueprint, request
from app.config import Config, logging
from app.utils.errors import BadRequestError
from app.integrations.hubspot_api import HubSpotAPI
from app.services.oauth_manager import OAuthManager
from app.services.hubspot_service import HubSpotService
from app.utils.api_responses import build_success_response

hubspot_bp = Blueprint('hubspot', __name__)

# Initialize the managers globally or within a factory
oauth_manager = OAuthManager(
    client_id=Config.HUBSPOT_CLIENT_ID,
    client_secret=Config.HUBSPOT_CLIENT_SECRET,
    refresh_token=Config.HUBSPOT_REFRESH_TOKEN
)

hubspot_api = HubSpotAPI(oauth_manager=oauth_manager)
hubspot_service = HubSpotService(hubspot_api=hubspot_api)

@hubspot_bp.route('/contact', methods=['POST'])
def create_or_update_contact():
    """
    Endpoint to create or update a contact in HubSpot.
    """
    data = request.get_json()

    if not data:
        logging.error("No JSON payload provided")
        raise BadRequestError("No JSON payload provided")

    result, action = hubspot_service.create_or_update_contact(data)

    if action == "created":
        status_code = 201
        responseMessage = "Contact created successfully."
    else:
        status_code = 200
        responseMessage = "Contact updated successfully."

    return build_success_response(
        message=responseMessage,
        status=status_code,
        data=result
    )


@hubspot_bp.route('/deals', methods=['POST'])
def create_or_update_deals():
    """
    Endpoint to create/update one or more deals and associate them with a contact.
    """
    data = request.get_json()

    if not data:
        logging.error("No JSON payload provided")
        raise BadRequestError("No JSON payload provided.")

    contact_id = data.get("contactId")
    deals_data = data.get("deals", [])

    if not contact_id:
        raise BadRequestError("contactId is required.")
    
    if not isinstance(deals_data, list) or len(deals_data) == 0:
        raise BadRequestError("At least one deal object is required in 'deals' array.")

    # Call the service to handle creation/updating of deals
    results = hubspot_service.create_or_update_deals(contact_id, deals_data)

    # Build a user-friendly response
    formatted_results = []

    for deal_result, action in results:
        formatted_results.append({
            "action": action,
            "deal": deal_result
        })

    return build_success_response(
        message="Deals processed successfully.",
        data=formatted_results
    )