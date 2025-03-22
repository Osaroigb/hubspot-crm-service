from flask import Flask
from flask_cors import CORS
from flasgger import Swagger

# Initialize the Flask application
app = Flask(__name__)
cors = CORS(app)

# Configure Swagger
swagger_config = {
    "headers": [],
    "specs": [
        {
            "endpoint": 'apispec',
            "route": '/api-docs/apispec.json',
            "rule_filter": lambda rule: True,
            "model_filter": lambda tag: True,
        }
    ],
    "static_url_path": "/flasgger_static",
    "swagger_ui": True,
    "specs_route": "/api-docs/"
}

swagger_template = {
    "swagger": "2.0",
    "info": {
        "title": "HubSpot CRM Service API",
        "description": "API for managing HubSpot contacts, deals, tickets and more.",
        "version": "1.0.0"
    },
    "basePath": "/api/v1",  # Global base path
}

swagger = Swagger(app, config=swagger_config, template=swagger_template)

# Register Flask routes
from .routes import *