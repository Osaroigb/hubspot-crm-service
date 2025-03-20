from flask import Flask
from flask_cors import CORS

# Initialize the Flask application
app = Flask(__name__)
cors = CORS(app)

# Register Flask routes
from . import routes