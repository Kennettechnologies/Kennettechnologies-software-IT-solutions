import os
import json
import re
import bcrypt
from typing import Dict, Any
from dotenv import load_dotenv
from flask import Flask, request, jsonify, abort
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from sqlalchemy.exc import SQLAlchemyError

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

# Configure CORS with more restrictive settings
app.config['CORS_HEADERS'] = 'Content-Type'
app.config['CORS_RESOURCES'] = {r"/*": {"origins": "*"}}  # Adjust origins as needed

# Database configuration with error handling
try:
    db_user = os.getenv('DB_USER')
    db_password = os.getenv('DB_PASSWORD')
    db_host = os.getenv('DB_HOST')
    db_name = 'customer'

    if not all([db_user, db_password, db_host]):
        raise ValueError("Missing database configuration environment variables")

    app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+mysqlconnector://{db_user}:{db_password}@{db_host}:3306/{db_name}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_POOL_RECYCLE'] = 280
    app.config['SQLALCHEMY_POOL_TIMEOUT'] = 20

except Exception as e:
    print(f"Database configuration error: {e}")
    raise

# Initialize database
db = SQLAlchemy(app)

class Customer(db.Model):
    __tablename__ = 'customer'

    username = db.Column(db.String(50), primary_key=True)
    password = db.Column(db.String(255), nullable=False)  # Increased length for bcrypt hash
    companyName = db.Column(db.String(250), nullable=False)
    email = db.Column(db.String(150), nullable=False, unique=True)

    def __init__(self, username: str, password: str, companyName: str, email: str):
        self.username = username
        self.set_password(password)
        self.companyName = companyName
        self.email = email

    def set_password(self, password: str) -> None:
        """Securely hash the password."""
        if not self.is_valid_password(password):
            raise ValueError("Password does not meet complexity requirements")
        self.password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(rounds=12)).decode('utf-8')

    def check_password(self, password: str) -> bool:
        """Check if the provided password is correct."""
        return bcrypt.checkpw(password.encode('utf-8'), self.password.encode('utf-8'))

    def set_email(self, email: str) -> None:
        """Validate and set email."""
        if not self.is_valid_email(email):
            raise ValueError("Invalid email format")
        self.email = email

    @staticmethod
    def is_valid_password(password: str) -> bool:
        """Check password complexity."""
        return (
            len(password) >= 8 and  # Minimum length
            any(c.isupper() for c in password) and  # At least one uppercase
            any(c.islower() for c in password) and  # At least one lowercase
            any(c.isdigit() for c in password) and  # At least one digit
            any(not c.isalnum() for c in password)  # At least one special character
        )

    @staticmethod
    def is_valid_email(email: str) -> bool:
        """Validate email format."""
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(email_regex, email) is not None

    def json(self) -> Dict[str, str]:
        """Return a JSON-safe representation of the customer."""
        return {
            "username": self.username, 
            "companyName": self.companyName, 
            "email": self.email
        }  # Removed password from JSON output

@app.route("/User/<string:username>", methods=['POST'])
def addUser(username):
    # Validate input
    data = request.get_json()
    if not all(key in data for key in ['password', 'companyName', 'email']):
        return jsonify({"error": "Missing required fields"}), 400

    # Validate email format
    if '@' not in data['email'] or '.' not in data['email'].split('@')[-1]:
        return jsonify({"error": "Invalid email format"}), 400

    # Check if username or email already exists
    if Customer.query.filter_by(username=username).first():
        return jsonify({"error": f"Username '{username}' already exists"}), 409
    if Customer.query.filter_by(email=data['email']).first():
        return jsonify({"error": "Email already registered"}), 409

    try:
        # Create new user with hashed password
        customer = Customer(
            username=username,
            password=data['password'],
            companyName=data['companyName'],
            email=data['email']
        )
        db.session.add(customer)
        db.session.commit()
        return jsonify({
            "message": "Account created successfully",
            "username": username,
            "email": data['email']
        }), 201
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error creating user: {str(e)}")
        return jsonify({"error": "An error occurred while creating the account"}), 500

@app.route("/User", methods=['GET'])
def get_all():
    return jsonify({"users": [customer.json() for customer in Customer.query.all()]})

@app.route("/AUser/<string:username>", methods=["POST"])
def find_by_username(username):
    # Validate request
    if not request.is_json:
        return jsonify({"error": "Missing JSON in request"}), 400
    
    data = request.get_json()
    if 'password' not in data:
        return jsonify({"error": "Password is required"}), 400
    
    # Find user
    user = Customer.query.filter_by(username=username).first()
    if not user:
        # Don't reveal that the user doesn't exist
        return jsonify({"error": "Invalid username or password"}), 401
    
    # Verify password
    try:
        if user.check_password(data['password']):
            # Password is correct
            return jsonify({
                "message": "Authentication successful",
                "username": user.username,
                "email": user.email,
                "companyName": user.companyName
            }), 200
        else:
            return jsonify({"error": "Invalid username or password"}), 401
    except Exception as e:
        app.logger.error(f"Authentication error: {str(e)}")
        return jsonify({"error": "An error occurred during authentication"}), 500

if __name__ == '__main__':
    # Don't run in debug mode in production
    debug_mode = os.getenv('FLASK_ENV', 'development') == 'development'
    app.run(host='0.0.0.0', port=5001, debug=debug_mode)
