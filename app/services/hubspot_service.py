import logging
from marshmallow import ValidationError
from app.utils.errors import NotFoundError, UnprocessableEntityError
from app.schemas.hubspot_schema import ContactSchema, DealSchema, TicketSchema


CONTACTS_ENDPOINT = "/crm/v3/objects/contacts"
SEARCH_CONTACTS_ENDPOINT = "/crm/v3/objects/contacts/search"

DEALS_ENDPOINT = "/crm/v3/objects/deals"
SEARCH_DEALS_ENDPOINT = "/crm/v3/objects/deals/search"

TICKETS_ENDPOINT = "/crm/v3/objects/tickets"
SEARCH_TICKETS_ENDPOINT = "/crm/v3/objects/tickets/search"

class HubSpotService:
    def __init__(self, hubspot_api):
        """
        :param hubspot_api: An instance of HubSpotAPI.
        """
        self.hubspot_api = hubspot_api

        self.contact_schema = ContactSchema()
        self.deal_schema = DealSchema()
        self.ticket_schema = TicketSchema()


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
    

    def assert_contact_exists(self, contact_id: str):
        """
        Searches HubSpot for a contact with the contact_id.
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

        if results:
            if results[0]["archived"] is True:
                logging.error(f"Contact {contact_id} is archived in HubSpot.")
                raise NotFoundError(
                    message="Contact not found (archived in HubSpot).",
                    verboseMessage=f"Contact {contact_id} is archived."
                )
    
            contact_email = results[0]["properties"]["email"]
            logging.info(f"Valid contact found: ID={contact_id}, email={contact_email}")
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

        :return: A list of results, where each entry is (deal_result, "created" or "updated")
        """      
        # verify the contact exists (and not archived)
        self.assert_contact_exists(contact_id)
        
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
            endpoint=SEARCH_DEALS_ENDPOINT,
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


    def create_tickets(self, contact_id: str, deal_ids: list[str], tickets_data: list[dict]):
        """
        Creates one or more new tickets in HubSpot, always new (never update).
        Associates each ticket with the specified contact and deals.
    
        :return: A list of (ticket_response, "created").
        """
        # verify the contact exists (and not archived)
        self.assert_contact_exists(contact_id)

        # verify each deal exists
        for deal_id in deal_ids:
            self.assert_deal_exists(deal_id)

        results = []

        for ticket_payload in tickets_data:
            # Validate mandatory fields
            try:
                valid_ticket_data = self.ticket_schema.load(ticket_payload)
            except ValidationError as err:
                logging.error(f"Invalid ticket data: {err.messages}")

                raise UnprocessableEntityError(
                    message="Invalid ticket data",
                    verboseMessage=err.messages
                )
            
            created_ticket = self.create_ticket(valid_ticket_data, contact_id, deal_ids)
            new_ticket_id = created_ticket.get("id")

            # Associate ticket with contact
            self.associate_ticket_with_contact(new_ticket_id, contact_id)

            # Associate ticket with each deal
            for deal_id in deal_ids:
                self.associate_ticket_with_deal(new_ticket_id, deal_id)

            results.append((created_ticket, "created"))

        return results


    def create_ticket(self, ticket_data: dict, contact_id: str, deal_ids: list[str]):
        """
        Creates a new ticket in HubSpot from the provided data.
        """
        payload = {
            "properties": ticket_data,
        }

        response = self.hubspot_api.request(
            method="POST",
            endpoint=TICKETS_ENDPOINT,
            json_data=payload
        )

        ticket_id = response.get("id")
        logging.info(f"Created new ticket '{ticket_data.get('subject')}' with ID: {ticket_id}")
        return response


    def associate_ticket_with_contact(self, ticket_id: str, contact_id: str):
        """
        Associates an existing ticket with a contact in HubSpot.
        """
        association_url = f"/crm/v3/objects/tickets/{ticket_id}/associations/contacts/{contact_id}/ticket_to_contact"

        body = [
            {
                "associationCategory": "HUBSPOT_DEFINED",
                "associationTypeId": 15
            }
        ]

        self.hubspot_api.request("PUT", association_url, json_data=body)
        logging.info(f"Associated ticket {ticket_id} with contact {contact_id}.")


    def associate_ticket_with_deal(self, ticket_id: str, deal_id: str):
        """
        Associates an existing ticket with an existing deal in HubSpot.
        """
        association_url = f"/crm/v3/objects/tickets/{ticket_id}/associations/deals/{deal_id}/ticket_to_deal"

        body = [
            {
                "associationCategory": "HUBSPOT_DEFINED",
                "associationTypeId": 26
            }
        ]

        self.hubspot_api.request("PUT", association_url, json_data=body)
        logging.info(f"Associated ticket {ticket_id} with deal {deal_id}.")


    def assert_deal_exists(self, deal_id: str):
        """
        Searches HubSpot for a deal with the deal_id.
        """
        endpoint = f"{DEALS_ENDPOINT}/{deal_id}"

        try:
            response = self.hubspot_api.request(
                method="GET",
                endpoint=endpoint
            )

            # Access properties safely
            deal_name = response.get("properties", {}).get("dealname", "Unknown Deal")
            logging.info(f"Verified deal with name {deal_name} and ID {deal_id} exists.")

        except Exception as e:
            logging.error(f"Deal {deal_id} not found")
            raise NotFoundError(
                message="Deal not found.",
                verboseMessage=f"Deal {deal_id} not found."
            )


    def retrieve_new_crm_objects(self, created_after: str, limit: int = 10, after: str = None):
        """
        High-level method to retrieve newly created contacts, deals, tickets since 'created_after'.
        :param created_after: e.g. "2025-03-20T00:00:00Z"
        :param limit: max items
        :param after: optional paging cursor
        """
        new_contacts = self.search_new_contacts(created_after, limit, after)
        new_deals = self.search_new_deals(created_after, limit, after)
        new_tickets = self.search_new_tickets(created_after, limit, after)

        # embed deals in each contact object
        for contact in new_contacts.get("results", []):
            contact_id = contact.get("id")

            if contact_id:
                associated_deals = self.fetch_associated_deals_for_contact(contact_id)
                contact["associatedDeals"] = associated_deals

        return {
            "contacts": new_contacts.get("results", []),
            "contacts_paging": new_contacts.get("paging"),
            "deals": new_deals.get("results", []),
            "deals_paging": new_deals.get("paging"),
            "tickets": new_tickets.get("results", []),
            "tickets_paging": new_tickets.get("paging")
        }


    def search_new_contacts(self, created_after: str, limit: int, after: str):
        """
        Filter on createdate >= created_after
        """
        payload = {
            "filterGroups": [
                {
                    "filters": [
                        {
                            "propertyName": "createdate",
                            "operator": "GTE",
                            "value": created_after
                        }
                    ]
                }
            ],
            "properties": ["email", "firstname", "lastname", "phone", "createdate"],
            "limit": limit
        }

        if after:
            payload["after"] = after

        response = self.hubspot_api.request("POST", SEARCH_CONTACTS_ENDPOINT, json_data=payload)
        return response


    def search_new_deals(self, created_after: str, limit: int, after: str):
        """
        Filter on createdate >= created_after
        """
        payload = {
            "filterGroups": [
                {
                    "filters": [
                        {
                            "propertyName": "createdate",
                            "operator": "GTE",
                            "value": created_after
                        }
                    ]
                }
            ],
            "properties": ["dealname", "amount", "dealstage", "createdate"],
            "limit": limit
        }
        if after:
            payload["after"] = after

        response = self.hubspot_api.request("POST", SEARCH_DEALS_ENDPOINT, json_data=payload)
        return response


    def search_new_tickets(self, created_after: str, limit: int, after: str):
        """
        Filter on createdate >= created_after
        """
        payload = {
            "filterGroups": [
                {
                    "filters": [
                        {
                            "propertyName": "createdate",
                            "operator": "GTE",
                            "value": created_after
                        }
                    ]
                }
            ],
            "properties": ["subject", "description", "category", "pipeline", "hs_ticket_priority", "hs_pipeline_stage"],
            "limit": limit
        }

        if after:
            payload["after"] = after

        response = self.hubspot_api.request("POST", SEARCH_TICKETS_ENDPOINT, json_data=payload)
        return response
    

    def fetch_associated_deals_for_contact(self, contact_id: str) -> list:
        """
        Retrieve associated deal IDs for a single contact, then fetch each deal's details.
        Returns a list of deal objects (similar to your 'deals' format).
        """
        assoc_endpoint = f"/crm/v3/objects/contacts/{contact_id}/associations/deals"
        assoc_response = self.hubspot_api.request("GET", assoc_endpoint)

        associated_deal_ids = [item["id"] for item in assoc_response.get("results", [])]

        if not associated_deal_ids:
            return []

        deals = []

        for deal_id in associated_deal_ids:
            deal_endpoint = f"/crm/v3/objects/deals/{deal_id}?properties=dealname,amount,dealstage,createdate"
            deal_response = self.hubspot_api.request("GET", deal_endpoint)
            deals.append(deal_response)
        
        return deals