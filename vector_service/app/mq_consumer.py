import pika
import json
import os
from dotenv import load_dotenv
from app.service import process_cv_for_embedding

load_dotenv()

RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "localhost")
RABBITMQ_PORT = int(os.getenv("RABBITMQ_PORT", "5672"))
RABBITMQ_QUEUE = os.getenv("RABBITMQ_QUEUE", "cv_embedding_queue")

def callback(ch, method, properties, body):
    """
    Process CV when message received from RabbitMQ
    """
    try:
        data = json.loads(body)
        cv_id = data.get("cv_id")
        
        if not cv_id:
            print("Error: No cv_id in message")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
            return
        
        print(f"Received cv_id from RabbitMQ: {cv_id}")
        
        # Process CV (fetch, chunk, embed, upload to Pinecone)
        process_cv_for_embedding(cv_id)
        
        # Acknowledge message (remove from queue)
        ch.basic_ack(delivery_tag=method.delivery_tag)
        print(f"Successfully processed cv_id: {cv_id}")
        
    except Exception as e:
        print(f"Error processing message: {e}")
        # Reject and requeue for retry
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

def start_consumer():
    """
    Start RabbitMQ consumer in background
    Listens for cv.created events and processes them
    """
    try:
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(host=RABBITMQ_HOST, port=RABBITMQ_PORT)
        )
        channel = connection.channel()
        
        # Declare queue (must match publisher)
        channel.queue_declare(queue=RABBITMQ_QUEUE, durable=True)
        
        # Fair dispatch (don't give more than 1 message to worker at a time)
        channel.basic_qos(prefetch_count=1)
        
        # Start consuming
        channel.basic_consume(
            queue=RABBITMQ_QUEUE,
            on_message_callback=callback
        )
        
        print(f"VectorService consumer started. Waiting for messages on queue: {RABBITMQ_QUEUE}")
        print(f"RabbitMQ host: {RABBITMQ_HOST}:{RABBITMQ_PORT}")
        
        # Start consuming (blocking call)
        channel.start_consuming()
        
    except Exception as e:
        print(f"Failed to start RabbitMQ consumer: {e}")
        print("Make sure RabbitMQ is running!")
