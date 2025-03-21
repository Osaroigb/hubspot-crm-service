from marshmallow import Schema, fields, INCLUDE, validate

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
    amount = fields.Float(required=True, validate=validate.Range(min=0))
    dealstage = fields.Str(required=True)

    class Meta:
        unknown = INCLUDE 