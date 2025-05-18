# Create Payment Using PayPal Sample
# This sample code demonstrates how you can process a
# PayPal Account based Payment.
# API used: /v1/payments/payment


#library used: pip install paypalrestsdk

import os
import json
import logging
from functools import wraps
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from flask_cors import CORS, cross_origin
import paypalrestsdk
from paypalrestsdk import Payment, ResourceNotFound

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Configure CORS with specific origins and methods
CORS(app, resources={
    r"/*": {
        "origins": ["http://localhost:8000", "https://yourdomain.com"],
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configure PayPal
paypal_config = {
    'mode': os.getenv('PAYPAL_MODE', 'sandbox'),
    'client_id': os.getenv('PAYPAL_CLIENT_ID'),
    'client_secret': os.getenv('PAYPAL_SECRET')
}

# Validate PayPal configuration
if not all(paypal_config.values()):
    logger.error("Missing required PayPal configuration")
    raise ValueError("Missing required PayPal configuration")

paypalrestsdk.configure(paypal_config)

def json_response(func):
    """Decorator to standardize JSON responses and handle errors."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
            if isinstance(result, tuple) and len(result) == 2 and isinstance(result[1], int):
                response, status_code = result
                return jsonify(response), status_code
            return jsonify(result)
        except Exception as e:
            logger.error(f"Error in {func.__name__}: {str(e)}", exc_info=True)
            return jsonify({"error": "An unexpected error occurred"}), 500
    return wrapper

@app.route("/itemsBought/<string:paymentId>")
@cross_origin()
@json_response
def get_items(paymentId):
    """Retrieve payment details for a given payment ID."""
    try:
        # Input validation
        if not paymentId or not isinstance(paymentId, str):
            return {"error": "Invalid payment ID"}, 400
            
        # Retrieve payment details
        payment = Payment.find(paymentId)
        if not payment or not hasattr(payment, 'transactions') or not payment.transactions:
            return {"error": "Payment not found or has no transactions"}, 404
            
        # Extract and sanitize item list
        item_list = []
        for transaction in payment.transactions:
            if hasattr(transaction, 'item_list') and hasattr(transaction.item_list, 'items'):
                for item in transaction.item_list.items:
                    # Only include necessary fields
                    item_list.append({
                        'name': getattr(item, 'name', ''),
                        'quantity': getattr(item, 'quantity', 1),
                        'price': getattr(item, 'price', 0.0),
                        'currency': getattr(item, 'currency', 'SGD')
                    })
        
        return {"items": item_list}
        
    except ResourceNotFound:
        logger.warning(f"Payment not found: {paymentId}")
        return {"error": "Payment not found"}, 404
    except Exception as e:
        logger.error(f"Error retrieving payment {paymentId}: {str(e)}", exc_info=True)
        return {"error": "An error occurred while retrieving payment details"}, 500

@app.route("/payment/create", methods=["POST"])
@cross_origin()
@json_response
def create_payment():
    """Create a new PayPal payment."""
    try:
        # Validate request
        if not request.is_json:
            return {"error": "Missing JSON in request"}, 400
            
        data = request.get_json()
        if not data or 'items' not in data or not isinstance(data['items'], list):
            return {"error": "Invalid request format"}, 400
            
        # Calculate total amount and validate items
        total_amount = 0.0
        items = []
        
        for item in data['items']:
            try:
                price = float(item.get('price', 0))
                quantity = int(item.get('quantity', 1))
                if price < 0 or quantity <= 0:
                    raise ValueError("Invalid price or quantity")
                    
                total_amount += price * quantity
                items.append({
                    'name': str(item.get('name', 'Item')),
                    'price': f"{price:.2f}",
                    'quantity': quantity,
                    'currency': 'SGD',
                    'description': str(item.get('description', ''))
                })
            except (ValueError, TypeError) as e:
                logger.warning(f"Invalid item format: {item}")
                return {"error": f"Invalid item format: {item}"}, 400
        
        if total_amount <= 0:
            return {"error": "Total amount must be greater than zero"}, 400
            
        # Create payment
        payment = Payment({
            "intent": "sale",
            "payer": {"payment_method": "paypal"},
            "redirect_urls": {
                "return_url": os.getenv('PAYPAL_RETURN_URL', 'http://localhost:8000/payment/success'),
                "cancel_url": os.getenv('PAYPAL_CANCEL_URL', 'http://localhost:8000/payment/cancel')
            },
            "transactions": [{
                "item_list": {"items": items},
                "amount": {
                    "total": f"{total_amount:.2f}",
                    "currency": "SGD",
                    "details": {
                        "subtotal": f"{total_amount:.2f}"
                    }
                },
                "description": "Payment for products/services"
            }]
        })
        
        # Create payment and get approval URL
        if payment.create():
            for link in payment.links:
                if link.method == "REDIRECT":
                    return {
                        "payment_id": payment.id,
                        "approval_url": link.href
                    }
            return {"error": "No redirect URL found"}, 500
        else:
            logger.error(f"Payment creation failed: {payment.error}")
            return {"error": "Payment creation failed", "details": str(payment.error)}, 400
            
    except Exception as e:
        logger.error(f"Error creating payment: {str(e)}", exc_info=True)
        return {"error": "An error occurred while creating payment"}, 500

@app.route('/payment/execute', methods=['POST'])
@cross_origin()
@json_response
def execute_payment():
    """Execute an approved PayPal payment."""
    try:
        if not request.is_json:
            return {"error": "Missing JSON in request"}, 400
            
        data = request.get_json()
        payment_id = data.get('paymentId')
        payer_id = data.get('PayerID')
        
        if not payment_id or not payer_id:
            return {"error": "Missing paymentId or PayerID"}, 400
        
        # Find and execute the payment
        payment = Payment.find(payment_id)
        if not payment:
            return {"error": "Payment not found"}, 404
            
        if payment.state == 'approved':
            return {
                "status": "already_approved",
                "payment_id": payment.id,
                "state": payment.state
            }
            
        if payment.execute({"payer_id": payer_id}):
            logger.info(f"Payment {payment_id} executed successfully")
            return {
                "status": "success",
                "payment_id": payment.id,
                "state": payment.state,
                "transactions": [{
                    "amount": t.amount.total,
                    "currency": t.amount.currency,
                    "description": t.description
                } for t in payment.transactions] if hasattr(payment, 'transactions') else []
            }
        else:
            logger.error(f"Payment execution failed: {payment.error}")
            return {
                "status": "failed",
                "error": str(payment.error)
            }, 400
            
    except ResourceNotFound:
        return {"error": "Payment not found"}, 404
    except Exception as e:
        logger.error(f"Error executing payment: {str(e)}", exc_info=True)
        return {"error": "An error occurred while executing payment"}, 500

if __name__ == '__main__':
    # Don't run in debug mode in production
    debug_mode = os.getenv('FLASK_ENV', 'development') == 'development'
    port = int(os.getenv('PORT', 5000))
    
    if debug_mode:
        app.run(host='0.0.0.0', port=port, debug=False)
    else:
        # Use Gunicorn in production
        from gunicorn.app.base import BaseApplication
        
        class StandaloneApplication(BaseApplication):
            def __init__(self, app, options=None):
                self.application = app
                self.options = options or {}
                super().__init__()
                
            def load_config(self):
                config = {key: value for key, value in self.options.items()
                        if key in self.cfg.settings and value is not None}
                for key, value in config.items():
                    self.cfg.set(key.lower(), value)
                    
            def load(self):
                return self.application
                
        # Gunicorn config
        options = {
            'bind': f'0.0.0.0:{port}',
            'workers': 4,
            'worker_class': 'gevent',
            'timeout': 120,
            'log_level': 'info',
            'accesslog': '-',
            'errorlog': '-',
            'capture_output': True
        }
        
        StandaloneApplication(app, options).run()