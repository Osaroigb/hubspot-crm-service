from marshmallow import Schema, validate, fields, INCLUDE, validates, ValidationError

class ContactSchema(Schema):
    """
    Marshmallow schema for validating contact payload.
    Additional fields are allowed and handled dynamically.
    """
    email = fields.Email(required=True)
    firstname = fields.Str(required=True)
    lastname = fields.Str(required=True)
    phone = fields.Str(required=True)
    
    class Meta:
        unknown = INCLUDE  # Allow unknown fields, so dynamic fields are not dropped


class DealSchema(Schema):
    """
    Marshmallow schema for validating deal payload.
    Additional fields are allowed and handled dynamically.
    """
    dealname = fields.Str(required=True)
    amount = fields.Float(required=True, validate=validate.Range(min=1))
    dealstage = fields.Str(required=True)

    class Meta:
        unknown = INCLUDE 


class TicketSchema(Schema):
    """
    Marshmallow schema for validating support ticket payloads.
    """
    subject = fields.Str(required=True)
    description = fields.Str(required=True)
    category = fields.Str(required=True)
    pipeline = fields.Str(required=True)
    hs_ticket_priority = fields.Str(required=True)
    hs_pipeline_stage = fields.Str(required=True)

    # The category must be one of the specified enums
    VALID_CATEGORIES = {
        "general_inquiry",
        "technical_issue",
        "billing",
        "service_request",
        "meeting"
    }

    @validates("category")
    def validate_category(self, value):

        if value not in self.VALID_CATEGORIES:
            raise ValidationError(f"Invalid category. Must be one of {list(self.VALID_CATEGORIES)}")

    class Meta:
        unknown = INCLUDE