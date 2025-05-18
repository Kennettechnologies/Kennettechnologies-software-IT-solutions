import os
import json
import logging
import pika
import requests
import time
from functools import wraps
from dotenv import load_dotenv
from datetime import datetime
from typing import Dict, Any, Tuple

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
MAILGUN_API_KEY = os.getenv('MAILGUN_API_KEY')
MAILGUN_DOMAIN = os.getenv('MAILGUN_DOMAIN', 'sandbox2257105e012e438cab8c6547d9de3687.mailgun.org')
MAILGUN_BASE_URL = f"https://api.mailgun.net/v3/{MAILGUN_DOMAIN}/messages"

# Validate configuration
if not MAILGUN_API_KEY:
    logger.error("MAILGUN_API_KEY environment variable is not set")
    raise ValueError("MAILGUN_API_KEY environment variable is required")

def log_activity(message: str, level: str = 'info', **kwargs: Any) -> None:
    """Helper function for consistent logging."""
    log_entry = {
        'timestamp': datetime.utcnow().isoformat(),
        'message': message,
        **kwargs
    }
    
    if level.lower() == 'error':
        logger.error(json.dumps(log_entry))
    else:
        logger.info(json.dumps(log_entry))

def send_notification(data: Dict[str, Any]) -> Tuple[str, int]:
    """
    Send email notification using Mailgun API.
    
    Args:
        data (dict): Dictionary containing email details
            Required keys: 'to', 'subject', 'text'
            Optional keys: 'from', 'html', 'cc', 'bcc'
    
    Returns:
        tuple: (status_message, status_code)
    """
    try:
        # Validate input
        if not isinstance(data, dict):
            raise ValueError("Data must be a dictionary")
            
        required_fields = ['to', 'subject', 'text']
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Missing required field: {field}")
        
        # Prepare email data
        email_data = {
            'from': data.get('from', f'B.Y. Solutions <noreply@{MAILGUN_DOMAIN}>'),
            'to': data['to'],
            'subject': data['subject'],
            'text': data['text']
        }
        
        # Add optional fields if present
        if 'html' in data:
            email_data['html'] = data['html']
        if 'cc' in data:
            email_data['cc'] = data['cc']
        if 'bcc' in data:
            email_data['bcc'] = data['bcc']
        
        # Log the email being sent (without sensitive data)
        log_data = email_data.copy()
        if 'text' in log_data:
            log_data['text'] = '[content redacted]'  # Don't log full email content
        log_activity("Sending email notification", **log_data)
        
        # Send the email
        response = requests.post(
            MAILGUN_BASE_URL,
            auth=("api", MAILGUN_API_KEY),
            data=email_data,
            timeout=10  # 10 seconds timeout
        )
        
        # Check response
        if response.status_code == 200:
            log_activity("Email sent successfully", 
                        recipient=email_data['to'], 
                        subject=email_data['subject'][:50] + '...')
            return "Successfully Sent", response.status_code
        else:
            error_msg = f"Failed to send email: {response.status_code} - {response.text}"
            log_activity(error_msg, level='error', 
                        status_code=response.status_code,
                        response=response.text)
            return "Sending Failed", response.status_code
            
    except requests.exceptions.RequestException as e:
        error_msg = f"Mailgun API request failed: {str(e)}"
        log_activity(error_msg, level='error', error_type=type(e).__name__)
        return f"Error: {str(e)}", 500
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        log_activity(error_msg, level='error', error_type=type(e).__name__)
        return f"Error: {str(e)}", 500


def setup_rabbitmq_connection() -> pika.BlockingConnection:
    """Set up and return a RabbitMQ connection with error handling."""
    try:
        # Get RabbitMQ configuration from environment variables
        rabbitmq_host = os.getenv('RABBITMQ_HOST', 'localhost')
        rabbitmq_port = int(os.getenv('RABBITMQ_PORT', '5672'))
        rabbitmq_user = os.getenv('RABBITMQ_USER', 'guest')
        rabbitmq_password = os.getenv('RABBITMQ_PASSWORD', 'guest')
        rabbitmq_vhost = os.getenv('RABBITMQ_VHOST', '/')
        
        # Connection parameters
        credentials = pika.PlainCredentials(rabbitmq_user, rabbitmq_password)
        parameters = pika.ConnectionParameters(
            host=rabbitmq_host,
            port=rabbitmq_port,
            virtual_host=rabbitmq_vhost,
            credentials=credentials,
            heartbeat=600,
            blocked_connection_timeout=300
        )
        
        # Establish connection
        connection = pika.BlockingConnection(parameters)
        log_activity("Successfully connected to RabbitMQ")
        return connection
        
    except Exception as e:
        log_activity(f"Failed to connect to RabbitMQ: {str(e)}", level='error')
        raise

def setup_rabbitmq_infrastructure(channel: pika.adapters.blocking_connection.BlockingChannel) -> None:
    """Set up RabbitMQ exchanges, queues, and bindings."""
    try:
        # Exchange and queue names
        exchange_name = os.getenv('RABBITMQ_EXCHANGE', 'order_topic')
        queue_name = os.getenv('RABBITMQ_QUEUE', 'notification')
        routing_key = os.getenv('RABBITMQ_ROUTING_KEY', 'notification.#')
        
        # Declare exchange
        channel.exchange_declare(
            exchange=exchange_name,
            exchange_type='topic',
            durable=True
        )
        
        # Declare queue with dead letter exchange
        channel.queue_declare(
            queue=queue_name,
            durable=True,
            arguments={
                'x-dead-letter-exchange': f'{exchange_name}_dlx',
                'x-message-ttl': 60000  # 1 minute TTL for messages
            }
        )
        
        # Bind queue to exchange
        channel.queue_bind(
            exchange=exchange_name,
            queue=queue_name,
            routing_key=routing_key
        )
        
        # Set quality of service
        channel.basic_qos(prefetch_count=1)
        
        log_activity("RabbitMQ infrastructure set up successfully")
        
    except Exception as e:
        log_activity(f"Failed to set up RabbitMQ infrastructure: {str(e)}", level='error')
        raise

def start_consumer() -> None:
    """Start the RabbitMQ consumer with reconnection logic."""
    max_retries = 5
    retry_delay = 5  # seconds
    
    for attempt in range(1, max_retries + 1):
        try:
            # Set up connection and channel
            connection = setup_rabbitmq_connection()
            channel = connection.channel()
            
            # Set up infrastructure
            setup_rabbitmq_infrastructure(channel)
            
            # Set up consumer
            queue_name = os.getenv('RABBITMQ_QUEUE', 'notification')
            channel.basic_consume(
                queue=queue_name,
                on_message_callback=callback_wrapper,
                auto_ack=False  # Manual acknowledgment
            )
            
            log_activity("Notification service started. Waiting for messages...")
            
            # Start consuming
            channel.start_consuming()
            
        except pika.exceptions.AMQPConnectionError as e:
            if attempt == max_retries:
                log_activity(f"Failed to connect to RabbitMQ after {max_retries} attempts. Giving up.", level='error')
                raise
            log_activity(f"Connection attempt {attempt} failed. Retrying in {retry_delay} seconds...", level='warning')
            time.sleep(retry_delay)
            retry_delay *= 2  # Exponential backoff
            
        except Exception as e:
            log_activity(f"Unexpected error: {str(e)}", level='error')
            if 'connection' in locals() and connection.is_open:
                connection.close()
            if attempt == max_retries:
                raise
            time.sleep(retry_delay)
            
        finally:
            if 'connection' in locals() and connection.is_open:
                connection.close()


def callback_wrapper(channel: pika.adapters.blocking_connection.BlockingChannel, 
                     method: pika.spec.Basic.Deliver, 
                     properties: pika.spec.BasicProperties, 
                     body: bytes) -> None:
    """Wrapper for the callback function with error handling and message acknowledgment."""
    try:
        # Parse message body
        try:
            message = json.loads(body)
            log_activity("Received message", message_id=properties.message_id)
        except json.JSONDecodeError:
            log_activity("Failed to decode message body", level='error', body=body)
            channel.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
            return
        
        # Process the message
        callback(channel, method, properties, message)
        
        # Acknowledge message if no exceptions were raised
        channel.basic_ack(delivery_tag=method.delivery_tag)
        
    except Exception as e:
        log_activity("Error processing message", 
                    level='error', 
                    error=str(e), 
                    message_id=getattr(properties, 'message_id', 'unknown'))
        
        # Negative acknowledgment - don't requeue to avoid poison messages
        channel.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

def callback(channel: pika.adapters.blocking_connection.BlockingChannel, 
             method: pika.spec.Basic.Deliver, 
             properties: pika.spec.BasicProperties, 
             message: Dict[str, Any]) -> None:
    """Process incoming messages from RabbitMQ."""
    try:
        # Log receipt of message
        booking_id = message.get('bookingID')
        if booking_id:
            log_activity("Processing booking notification", 
                        booking_id=booking_id,
                        routing_key=method.routing_key)
        else:
            log_activity("Processing notification", 
                        routing_key=method.routing_key)
        
        # Send notification
        result, status_code = send_notification(message)
        
        if status_code == 200:
            log_activity("Notification processed successfully", 
                        booking_id=booking_id,
                        status=result)
        else:
            log_activity("Failed to process notification", 
                        level='error',
                        booking_id=booking_id,
                        status=status_code,
                        error=result)
    
    except Exception as e:
        log_activity("Error in callback", 
                    level='error', 
                    error=str(e),
                    message=message)
        raise  # Re-raise to be caught by wrapper


if __name__ == "__main__":
    import time
    
    # Configure logging to file in production
    if os.getenv('FLASK_ENV') == 'production':
        from logging.handlers import RotatingFileHandler
        
        # Create logs directory if it doesn't exist
        log_dir = 'logs'
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        # Configure file handler
        file_handler = RotatingFileHandler(
            f'{log_dir}/notification_service.log',
            maxBytes=1024 * 1024 * 10,  # 10MB
            backupCount=5
        )
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        logger.addHandler(file_handler)
    
    log_activity("Starting notification service", 
                service=os.path.basename(__file__),
                environment=os.getenv('FLASK_ENV', 'development'))
    
    try:
        start_consumer()
    except KeyboardInterrupt:
        log_activity("Notification service stopped by user")
    except Exception as e:
        log_activity(f"Notification service crashed: {str(e)}", level='error')
        raise
