import logging
from marshmallow import ValidationError
from app.schemas.hubspot_schema import ContactSchema, DealSchema
from app.utils.errors import NotFoundError, UnprocessableEntityError


CONTACTS_ENDPOINT = "/crm/v3/objects/contacts"
SEARCH_CONTACTS_ENDPOINT = "/crm/v3/objects/contacts/search"

DEALS_SEARCH_ENDPOINT = "/crm/v3/objects/deals/search"
DEALS_ENDPOINT = "/crm/v3/objects/deals"

class HubSpotService:
    def __init__(self, hubspot_api):
        """
        :param hubspot_api: An instance of HubSpotAPI.
        """
        self.hubspot_api = hubspot_api
        self.contact_schema = ContactSchema()
        self.deal_schema = DealSchema()


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
    

    def find_contact_by_id(self, contact_id: str):
        """
        Searches HubSpot for a contact with the contact_id.
        :return: The contact email if found, else None.
        """
        payload = {
            "filterGroups": [
                {
                    "filters": [
                        {
                            "value": contact_id,
                            "propertyName": "vid",
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

        if results[0]["archived"] is True:
            logging.error(f"Contact {contact_id} is archived in HubSpot.")
            raise NotFoundError(
                message="Contact not found (archived in HubSpot).",
                verboseMessage=f"Contact {contact_id} is archived."
            )


        if results:
            contact_email = results[0]["properties"]["email"]
            return contact_email
        else:
            logging.error(f"Contact {contact_id} not found.")
            raise NotFoundError(
                message="Contact not found.",
                verboseMessage=f"Contact {contact_id} not found."
            )


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
    

    def create_or_update_deals(self, contact_id: str, deals_data: list):
        """
        Create or update one or more deals, then associate each deal with the specified contact.
        If the contact does not exist, raise a 404 NotFoundError and skip deal creation.

        :param contact_id: The HubSpot contact ID to associate deals with.
        :param deals_data: A list of deal dicts, each must have mandatory fields
        :return: A list of results, where each entry is (deal_result, "created" or "updated")
        """
        # Validate that the contact actually exists
        try:
            contact = self.find_contact_by_id(contact_id)
            logging.info(f"Valid contact found: ID={contact_id}, email={contact}")
        except NotFoundError as e:
            # If the contact doesn't exist, re-raise the 404 NotFoundError
            raise e
        

        results = []

        for deal_payload in deals_data:
            # Validate the deal fields
            try:
                valid_deal_data = self.deal_schema.load(deal_payload)
            except ValidationError as err:
                logging.error(f"Invalid deal data: {err.messages}")

                raise UnprocessableEntityError(
                    message="Invalid deal data",
                    verboseMessage=err.messages
                )

            dealname = valid_deal_data["dealname"]
            existing_deal_id = self.find_deal_by_name(dealname)

            if existing_deal_id:
                logging.info(f"Deal with name '{dealname}' found (ID: {existing_deal_id}). Updating...")
                updated_deal = self.update_deal(existing_deal_id, valid_deal_data)

                # Associate deal with contact (optional if not already associated)
                self.associate_deal_with_contact(existing_deal_id, contact_id)
                results.append((updated_deal, "updated"))
            else:
                logging.info(f"No existing deal with name '{dealname}'. Creating new deal...")
                created_deal = self.create_deal(valid_deal_data)
                new_deal_id = created_deal.get("id")

                # Associate newly created deal with contact
                self.associate_deal_with_contact(new_deal_id, contact_id)
                results.append((created_deal, "created"))

        return results


    def find_deal_by_name(self, dealname: str):
        """
        Searches HubSpot for a deal with the given 'dealname'.
        Returns the deal ID if found, else None.
        """
        payload = {
            "filterGroups": [
                {
                    "filters": [
                        {
                            "value": dealname,
                            "propertyName": "dealname",
                            "operator": "EQ"
                        }
                    ]
                }
            ],
            "properties": ["dealname", "amount", "dealstage"],
            "limit": 1
        }

        response = self.hubspot_api.request(
            method="POST",
            endpoint=DEALS_SEARCH_ENDPOINT,
            json_data=payload
        )

        results = response.get("results", [])

        if results:
            return results[0].get("id")
        return None


    def create_deal(self, deal_data: dict):
        """
        Creates a new deal in HubSpot using the provided deal_data.
        """
        payload = {"properties": deal_data}
        response = self.hubspot_api.request(
            method="POST",
            endpoint=DEALS_ENDPOINT,
            json_data=payload
        )

        deal_id = response.get("id")
        logging.info(f"Created new deal '{deal_data.get('dealname')}' with ID: {deal_id}")
        return response


    def update_deal(self, deal_id: str, deal_data: dict):
        """
        Updates an existing deal in HubSpot.
        """
        endpoint = f"{DEALS_ENDPOINT}/{deal_id}"
        payload = {"properties": deal_data}

        response = self.hubspot_api.request(
            method="PATCH",
            endpoint=endpoint,
            json_data=payload
        )

        logging.info(f"Updated deal '{deal_data.get('dealname')}' with ID: {deal_id}")
        return response


    def associate_deal_with_contact(self, deal_id: str, contact_id: str):
        """
        Associates an existing deal with a contact in HubSpot.
        The default type is 'deal_to_contact'.
        """
        association_url = "/crm/v3/associations/Deal/Contacts/batch/create"
        body = {
            "inputs": [
                {
                    "from": { "id": deal_id },
                    "to": { "id": contact_id },
                    "type": "deal_to_contact"
                }
            ]
        }

        self.hubspot_api.request(
            method="POST", 
            endpoint=association_url, 
            json_data=body
        )

        logging.info(f"Associated deal {deal_id} with contact {contact_id}.")