from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

# Configuration
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key')
app.config['DEBUG'] = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'

# Import routes
from routes.auth import auth_bp
from routes.products import products_bp
from routes.orders import orders_bp
from routes.customers import customers_bp
from routes.employees import employees_bp
from routes.bookings import bookings_bp
from routes.payments import payments_bp
from routes.notifications import notifications_bp
from routes.monitoring import monitoring_bp

# Register blueprints
app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(products_bp, url_prefix='/api/products')
app.register_blueprint(orders_bp, url_prefix='/api/orders')
app.register_blueprint(customers_bp, url_prefix='/api/customers')
app.register_blueprint(employees_bp, url_prefix='/api/employees')
app.register_blueprint(bookings_bp, url_prefix='/api/bookings')
app.register_blueprint(payments_bp, url_prefix='/api/payments')
app.register_blueprint(notifications_bp, url_prefix='/api/notifications')
app.register_blueprint(monitoring_bp, url_prefix='/api/monitoring')

@app.route('/')
def home():
    return jsonify({
        'status': 'success',
        'message': 'Welcome to Kennettechnologies API',
        'version': '1.0.0'
    })

@app.route('/health')
def health_check():
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat()
    })

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port) 