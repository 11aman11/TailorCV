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
    
    Args:
        cv_id: CV identifier (SHA256 hash)
    """
    try:
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(host=RABBITMQ_HOST, port=RABBITMQ_PORT)
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
        
        connection.close()
        print(f"Published cv_id to RabbitMQ: {cv_id}")
        
    except Exception as e:
        print(f"Failed to publish to RabbitMQ: {e}")
        # Don't raise - allow CV storage to succeed even if RabbitMQ is down
