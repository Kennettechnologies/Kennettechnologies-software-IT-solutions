from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
import jwt
from functools import wraps

auth_bp = Blueprint('auth', __name__)

# Mock user database (replace with actual database)
users_db = {}

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401
        try:
            token = token.split(' ')[1]  # Remove 'Bearer ' prefix
            data = jwt.decode(token, 'your-secret-key', algorithms=['HS256'])
            current_user = users_db.get(data['username'])
            if not current_user:
                return jsonify({'message': 'Invalid token!'}), 401
        except:
            return jsonify({'message': 'Invalid token!'}), 401
        return f(current_user, *args, **kwargs)
    return decorated

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'message': 'Missing required fields'}), 400
        
    if data['username'] in users_db:
        return jsonify({'message': 'Username already exists'}), 400
        
    users_db[data['username']] = {
        'username': data['username'],
        'password': data['password'],  # In production, hash the password
        'email': data.get('email', ''),
        'created_at': datetime.utcnow()
    }
    
    return jsonify({'message': 'User registered successfully'}), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'message': 'Missing credentials'}), 400
        
    user = users_db.get(data['username'])
    if not user or user['password'] != data['password']:  # In production, verify hashed password
        return jsonify({'message': 'Invalid credentials'}), 401
        
    token = jwt.encode({
        'username': user['username'],
        'exp': datetime.utcnow() + timedelta(hours=24)
    }, 'your-secret-key')
    
    return jsonify({
        'token': token,
        'user': {
            'username': user['username'],
            'email': user['email']
        }
    })

@auth_bp.route('/profile', methods=['GET'])
@token_required
def profile(current_user):
    return jsonify({
        'username': current_user['username'],
        'email': current_user['email'],
        'created_at': current_user['created_at'].isoformat()
    }) 