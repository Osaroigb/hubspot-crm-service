from . import app
from flask import request
from .config import logging
from .utils.errors import BaseError
from .utils.rate_limiting import RateLimiter
from app.controllers.hubspot_controller import hubspot_bp
from .utils.api_responses import build_error_response, build_success_response


# Global API prefix
API_PREFIX = "/api/v1"

rate_limiter = RateLimiter()

@app.before_request
def check_rate_limiting():
    ip = request.remote_addr

    if rate_limiter.is_rate_limited(ip):
        logging.error("Rate limit exceeded")
        return build_error_response(message="Rate limit exceeded", status=429)
    

@app.route("/favicon.ico")
def favicon():
    """Handle favicon requests to prevent 404 errors."""
    return "", 204


# Define the home route
@app.route(API_PREFIX, methods=['GET'])
def home():
    return build_success_response(message="Welcome to hubspot-crm-service")


# Register the HubSpot routes
app.register_blueprint(hubspot_bp, url_prefix=API_PREFIX + "/hubspot")


# Error handler for undefined routes
@app.errorhandler(404)
def not_found(error):
    if request.path.startswith('/flasgger_static'):
        return "", 204
    
    logging.error("Route not found")
    return build_error_response(message="Route not found", status=404)


@app.errorhandler(Exception)
def handle_exception(error):
    """
    Global error handler that checks if the error is a custom BaseError
    and uses its properties. Otherwise, returns a generic 500.
    """
    # Log the error for debugging
    logging.error(f"Unhandled exception: {error}", exc_info=True)

    if isinstance(error, BaseError):
        # A custom error we explicitly raised
        return build_error_response(
            message=error.message, 
            status=error.httpCode, 
            data=error.verboseMessage
        )
    else:
        # Default fallback for any other exceptions
        return build_error_response(
            message="Internal Server Error",
            status=500,
            data=str(error)
        )