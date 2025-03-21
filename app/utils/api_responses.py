from flask import jsonify

def build_success_response(message, status=200, data=None):
    """Build a standardized success response."""

    response = jsonify({
        'success': True,
        'message': message,
        'status_code': status,
        'data': data or {}
    })

    # Set the status code using the response object
    response.status_code = status
    return response


def build_error_response(message, status=400, data=None):
    """Build a standardized error response."""

    response = jsonify({
        'success': False,
        'error_message': message,
        'status_code': status,
        'data': data or {}
    })

    response.status_code = status
    return response