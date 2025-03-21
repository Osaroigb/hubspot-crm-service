import logging
from marshmallow import ValidationError
from app.schemas.hubspot_schema import ContactSchema
from app.utils.errors import UnprocessableEntityError

CONTACTS_ENDPOINT = "/crm/v3/objects/contacts"
SEARCH_CONTACTS_ENDPOINT = "/crm/v3/objects/contacts/search"

class HubSpotService:
    def __init__(self, hubspot_api):
        """
        :param hubspot_api: An instance of HubSpotAPI.
        """
        self.hubspot_api = hubspot_api
        self.contact_schema = ContactSchema()


    def create_or_update_contact(self, data: dict):
        """
        Create or update a contact in HubSpot based on email.
        :param data: Dict with contact details (must include mandatory fields).
        :return: (result_dict, action_str) => (HubSpot contact JSON, 'created' or 'updated')
        """
        # Validate input data
        try:
            valid_data = self.contact_schema.load(data)
        except ValidationError as err:
            logging.error(f"Invalid contact data: {err.messages}")
            raise UnprocessableEntityError("Invalid contact data.", verboseMessage=err.messages)

        email = valid_data["email"]

        # Check if contact exists
        existing_contact_id = self.find_contact_by_email(email)

        if existing_contact_id:
            logging.info(f"Contact with email {email} found. Updating...")
            updated = self.update_contact(existing_contact_id, valid_data)
            
            return updated, "updated"
        else:
            logging.info(f"No existing contact with email {email}. Creating new contact...")
            created = self.create_contact(valid_data)

            return created, "created"


    def find_contact_by_email(self, email: str):
        """
        Searches HubSpot for a contact with the given email.
        :return: The contact ID if found, else None.
        """
        payload = {
            "filterGroups": [
                {
                    "filters": [
                        {
                            "value": email,
                            "propertyName": "email",
                            "operator": "EQ"
                        }
                    ]
                }
            ],
            "properties": ["email", "firstname", "lastname", "phone"],
            "limit": 1
        }

        response = self.hubspot_api.request(
            method="POST",
            endpoint=SEARCH_CONTACTS_ENDPOINT,
            json_data=payload
        )

        results = response.get("results", [])
        if results:
            return results[0].get("id")
        
        return None


    def create_contact(self, valid_data: dict):
        """
        Creates a new contact in HubSpot.
        :return: Created contact data (dict).
        """
        # HubSpot expects properties in "properties" object
        payload = {"properties": valid_data}
        response = self.hubspot_api.request(
            method="POST",
            endpoint=CONTACTS_ENDPOINT,
            json_data=payload
        )

        contact_id = response.get("id")

        logging.info(f"Created new contact with ID: {contact_id}")
        return response


    def update_contact(self, contact_id: str, valid_data: dict):
        """
        Updates an existing contact in HubSpot.
        :return: Updated contact data (dict).
        """
        payload = {"properties": valid_data}
        endpoint = f"{CONTACTS_ENDPOINT}/{contact_id}"

        response = self.hubspot_api.request(
            method="PATCH",
            endpoint=endpoint,
            json_data=payload
        )

        logging.info(f"Updated contact with ID: {contact_id}")
        return response