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
    Expects JSON payload
    """
    data = request.get_json()

    if not data:
        logging.error("No JSON payload provided")
        raise BadRequestError("No JSON payload provided")

    result, action = hubspot_service.create_or_update_contact(data)

    if action == "created":
        responseMessage = "Contact created successfully."
    else:
        responseMessage = "Contact updated successfully."

    return build_success_response(
        message=responseMessage,
        data=result
    )