from . import app
from flask import jsonify

# Global API prefix
API_PREFIX = "/api/v1"

@app.route("/favicon.ico")
def favicon():
    """Handle favicon requests to prevent 404 errors."""
    return "", 204


# Define the home route
@app.route(API_PREFIX, methods=['GET'])
def home():
     return jsonify({
        'success': True,
        'message': "Welcome to hubspot-crm-service",
        'status_code': 200,
        'data': {}
    }), 200


# Error handler for undefined routes
@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'message': "Route not found",
        'status_code': 404,
        'data': {}
    }), 404