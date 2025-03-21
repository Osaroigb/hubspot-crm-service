from . import app
from flask import request
from .config import logging
from .utils.rate_limiting import RateLimiter
from .utils.api_responses import build_error_response, build_success_response
from .utils.errors import UnprocessableEntityError, NotFoundError, OperationForbiddenError


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


# Error handler for undefined routes
@app.errorhandler(404)
def not_found(error):
    logging.error("Route not found")
    return build_error_response(message="Route not found", status=404)


@app.errorhandler(Exception)
def handle_exception(error):
    # Log the error for debugging purposes
    logging.error(f"Unhandled exception: {error}")
    
    # Check the type of error and customize the response
    if isinstance(error, UnprocessableEntityError):
        response = {"error": error.message, "details": error.verboseMessage}
        http_code = error.httpCode

    elif isinstance(error, NotFoundError):
        response = {"error": error.message, "details": error.verboseMessage}
        http_code = error.httpCode

    elif isinstance(error, OperationForbiddenError):
        response = {"error": error.message, "details": error.verboseMessage}
        http_code = error.httpCode

    else:
        # Default error response if error type is not specifically handled
        response = {"error": "Internal Server Error", "details": "An unexpected error occurred"}
        http_code = 500
    
    return build_error_response(
        message=response["error"],
        status=http_code,
        data=response["details"]
    )