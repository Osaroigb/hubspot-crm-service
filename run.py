from flask import Flask, jsonify
from flask_cors import CORS

# Initialize the Flask application
app = Flask(__name__)
cors = CORS(app)

@app.route("/favicon.ico")
def favicon():
    """Handle favicon requests to prevent 404 errors."""
    return "", 204


# Define the home route
@app.route("/", methods=['GET'])
def home():
    return jsonify({
        'success': True,
        'message': "Welcome to hubspot-crm-service",
        'status_code': 200,
        'data': {}
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)