import pika
import json
import os
from dotenv import load_dotenv

load_dotenv()

RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "localhost")
RABBITMQ_PORT = int(os.getenv("RABBITMQ_PORT", "5672"))
RABBITMQ_QUEUE = os.getenv("RABBITMQ_QUEUE", "cv_embedding_queue")

def publish_cv_event(cv_id: str):
    """
    Publish cv_id to RabbitMQ for async embedding
    
    Creates a fresh connection each time and properly closes it.
    This is more reliable than connection reuse on Windows.
    
    Args:
        cv_id: CV identifier (SHA256 hash)
    """
    connection = None
    try:
        # Create connection
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(
                host=RABBITMQ_HOST,
                port=RABBITMQ_PORT,
                connection_attempts=3,
                retry_delay=2,
                socket_timeout=10
            )
        )
        channel = connection.channel()
        
        # Declare queue (durable = survives RabbitMQ restart)
        channel.queue_declare(queue=RABBITMQ_QUEUE, durable=True)
        
        # Publish message
        message = json.dumps({"cv_id": cv_id})
        channel.basic_publish(
            exchange='',
            routing_key=RABBITMQ_QUEUE,
            body=message,
            properties=pika.BasicProperties(
                delivery_mode=2  # Make message persistent
            )
        )
        
        print(f"Published cv_id to RabbitMQ: {cv_id}")
        
    except Exception as e:
        print(f"Failed to publish to RabbitMQ: {e}")
        # Don't raise - allow CV storage to succeed even if RabbitMQ is down
    finally:
        # Always close connection properly
        if connection and not connection.is_closed:
            try:
                connection.close()
            except:
                pass

def close_rabbitmq_connection():
    """Close RabbitMQ connection (called on shutdown) - no-op since we don't reuse connections"""
    pass
