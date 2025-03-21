from . import app
from .utils.api_responses import build_error_response, build_success_response


# Global API prefix
API_PREFIX = "/api/v1"

@app.route("/favicon.ico")
def favicon():
    """Handle favicon requests to prevent 404 errors."""
    return "", 204


# Define the home route
@app.route(API_PREFIX, methods=['GET'])
def home():
    return build_success_response(message="Welcome to hubspot-crm-service")


# Error handler for undefined routes
@app.errorhandler(404)
def not_found(error):
    return build_error_response(message="Route not found", status=404)