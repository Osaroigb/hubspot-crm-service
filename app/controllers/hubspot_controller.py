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
    Create or update a HubSpot contact.
    ---
    tags:
      - Contacts
    summary: Create or update a contact
    description: This endpoint checks if a contact with the provided email exists in HubSpot. If it exists, it updates the contact. Otherwise, it creates a new one.
    consumes:
      - application/json
    produces:
      - application/json
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - email
            - firstname
            - lastname
            - phone
          properties:
            email:
              type: string
              format: email
              example: johndoe@example.com
            firstname:
              type: string
              example: John
            lastname:
              type: string
              example: Doe
            phone:
              type: string
              example: "+123456789"
            extra_field:
              type: string
              example: Optional additional field (will be ignored if not defined in HubSpot)
    responses:
      200:
        description: Contact updated successfully
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            message:
              type: string
              example: Contact updated successfully.
            data:
              type: object
      201:
        description: Contact created successfully
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            message:
              type: string
              example: Contact created successfully.
            data:
              type: object
      400:
        description: Bad Request - Missing or invalid payload
      422:
        description: Validation Error - Missing required fields or invalid field types
      500:
        description: Internal Server Error
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
    Create or update one or more deals in HubSpot and associate them with a contact.
    ---
    tags:
      - Deals
    summary: Create or update multiple deals
    description: |
      This endpoint allows creating one or more deals in HubSpot if they don't exist, or updating them if they do.  
      All deals must be linked to the contact specified by `contactId`.

    consumes:
      - application/json
    produces:
      - application/json
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - contactId
            - deals
          properties:
            contactId:
              type: string
              description: ID of the contact to associate the deal(s) with
              example: "123456789"
            deals:
              type: array
              description: List of deals to create or update
              items:
                type: object
                required:
                  - dealname
                  - amount
                  - dealstage
                properties:
                  dealname:
                    type: string
                    example: "Website Revamp"
                  amount:
                    type: number
                    example: 1200.0
                  dealstage:
                    type: string
                    example: "appointmentscheduled"
                  extra_field:
                    type: string
                    example: "optional value that will be ignored if not recognized"
    responses:
      200:
        description: Deals processed successfully
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            message:
              type: string
              example: Deals processed successfully.
            data:
              type: array
              items:
                type: object
                properties:
                  action:
                    type: string
                    example: created
                  deal:
                    type: object
      400:
        description: Bad Request - Missing or invalid input
      422:
        description: Unprocessable Entity - Deal validation failed
      404:
        description: Contact not found
      500:
        description: Internal Server Error
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


@hubspot_bp.route('/tickets', methods=['POST'])
def create_tickets():
    """
    Create one or more support tickets and associate them with the specified contact and their deals.
    ---
    tags:
      - Tickets
    summary: Create one or more support tickets
    description: |
      This endpoint creates one or more support tickets in HubSpot, always as new (never updates).
      Each ticket is linked to the contact specified by `contactId` and all deals associated with that contact.

    consumes:
      - application/json
    produces:
      - application/json
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - contactId
            - tickets
          properties:
            contactId:
              type: string
              description: ID of the contact the ticket(s) will be associated with
              example: "123456789"
            tickets:
              type: array
              description: List of tickets to be created
              items:
                type: object
                required:
                  - subject
                  - description
                  - category
                  - pipeline
                  - hs_ticket_priority
                  - hs_pipeline_stage
                properties:
                  subject:
                    type: string
                    example: "Billing Issue - Payment Not Processed"
                  description:
                    type: string
                    example: "User was charged but did not receive confirmation."
                  category:
                    type: string
                    enum: ["general_inquiry", "technical_issue", "billing", "service_request", "meeting"]
                    example: "billing"
                  pipeline:
                    type: string
                    example: "support_pipeline_1"
                  hs_ticket_priority:
                    type: string
                    example: "HIGH"
                  hs_pipeline_stage:
                    type: string
                    example: "1"
                  extra_field:
                    type: string
                    example: "optional field for custom ticket properties"
    responses:
      200:
        description: Tickets created successfully
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            message:
              type: string
              example: Tickets created successfully.
            data:
              type: array
              items:
                type: object
                properties:
                  action:
                    type: string
                    example: created
                  ticket:
                    type: object
      400:
        description: Bad Request - Missing or invalid request payload
      404:
        description: Contact not found
      422:
        description: Validation Error - Missing required fields or invalid ticket data
      500:
        description: Internal Server Error
    """
    data = request.get_json()

    if not data:
        logging.error("No JSON payload provided")
        raise BadRequestError("No JSON payload provided.")

    contact_id = data.get("contactId")
    tickets_data = data.get("tickets", [])

    if not contact_id:
        raise BadRequestError("contactId is required.")
    if not isinstance(tickets_data, list) or len(tickets_data) == 0:
        raise BadRequestError("At least one ticket object is required in 'tickets' array.")

    results = hubspot_service.create_tickets(contact_id, tickets_data)
    response_list = []

    for (ticket, action) in results:
        response_list.append({
            "action": action,
            "ticket": ticket
        })

    return build_success_response(
        message="Tickets created successfully.",
        data=response_list
    )


@hubspot_bp.route('/new-crm-objects', methods=['GET'])
def get_new_crm_objects():
    """
    Retrieve newly created CRM contacts, deals, and tickets.
    ---
    tags:
      - CRM Data
    summary: Get new contacts, deals, and tickets since a given timestamp
    description: |
      This endpoint fetches newly created CRM objects (contacts, deals, and tickets) from HubSpot 
      based on the `since` timestamp. Supports pagination using the `after` parameter.
    produces:
      - application/json
    parameters:
      - in: query
        name: since
        type: string
        format: date-time
        required: true
        description: ISO timestamp to retrieve CRM objects created after this point (e.g., 2025-03-20T00:00:00Z)
        example: "2025-03-20T00:00:00Z"
      - in: query
        name: limit
        type: integer
        required: false
        default: 10
        description: Max number of items to return per type (contacts, deals, tickets)
      - in: query
        name: after
        type: string
        required: false
        description: Paging cursor (e.g., from previous response's paging.next.after)
    responses:
      200:
        description: Successfully retrieved new CRM objects
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            message:
              type: string
              example: Retrieved newly created CRM objects.
            data:
              type: object
              properties:
                contacts:
                  type: array
                  items:
                    type: object
                    description: Contact object with associated deals
                    properties:
                      id:
                        type: string
                      properties:
                        type: object
                      associatedDeals:
                        type: array
                        items:
                          type: object
                contacts_paging:
                  type: object
                  description: Pagination info for contacts
                deals:
                  type: array
                  items:
                    type: object
                deals_paging:
                  type: object
                tickets:
                  type: array
                  items:
                    type: object
                tickets_paging:
                  type: object
      400:
        description: Missing required query parameter
      500:
        description: Internal Server Error
    """
    since = request.args.get("since")
    limit = request.args.get("limit", default=10, type=int)
    after = request.args.get("after", default=None, type=str)

    if not since:
        raise BadRequestError("Query parameter 'since' is required, e.g. ?since=YYYY-MM-DDT00:00:00Z")

    result = hubspot_service.retrieve_new_crm_objects(since, limit, after)

    return build_success_response(
        message="Retrieved newly created CRM objects.",
        data=result
    )