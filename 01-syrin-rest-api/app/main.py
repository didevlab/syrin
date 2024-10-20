import logging
from flask import Flask, request, jsonify
import threading
import os
import pika
import json  # Import the JSON library

# Configure logging at INFO level
logging.basicConfig(level=logging.INFO)

# Disable debug logs from pika, setting it to WARNING or higher
logging.getLogger("pika").setLevel(logging.WARNING)

# Load RabbitMQ settings from environment variables
rabbitmq_host = os.getenv('RABBITMQ_HOST', '')
rabbitmq_port = int(os.getenv('RABBITMQ_PORT', 5672))
rabbitmq_vhost = os.getenv('RABBITMQ_VHOST', '')
rabbitmq_user = os.getenv('RABBITMQ_USER', '')
rabbitmq_pass = os.getenv('RABBITMQ_PASS', '')

app = Flask(__name__)

def declare_queues():
    """Function to declare the necessary queues when starting Flask."""
    # Connect to RabbitMQ
    credentials = pika.PlainCredentials(rabbitmq_user, rabbitmq_pass)
    parameters = pika.ConnectionParameters(
        host=rabbitmq_host,
        port=rabbitmq_port,
        virtual_host=rabbitmq_vhost,
        credentials=credentials
    )

    connection = pika.BlockingConnection(parameters)
    channel = connection.channel()

    # Declare the queues to ensure they exist
    queues = ['000_notification_warning', '000_notification_error']
    for queue in queues:
        channel.queue_declare(queue=queue, durable=True)
        logging.info(f"Queue '{queue}' checked or created.")

    connection.close()

def send_text_to_queue(text, level):
    # Connect to RabbitMQ
    credentials = pika.PlainCredentials(rabbitmq_user, rabbitmq_pass)
    parameters = pika.ConnectionParameters(
        host=rabbitmq_host,
        port=rabbitmq_port,
        virtual_host=rabbitmq_vhost,
        credentials=credentials
    )

    connection = pika.BlockingConnection(parameters)
    channel = connection.channel()

    # Construct the message in JSON format
    message = json.dumps({"text": text, "level": level})

    # Send the text to the corresponding queue
    channel.basic_publish(
        exchange='',
        routing_key='000_notification_' + level,
        body=message,
        properties=pika.BasicProperties(
            delivery_mode=2,  # Makes the message persistent
        )
    )

    # Close the connection
    connection.close()

@app.route('/api/text-to-speech', methods=['POST'])
def text_to_speech():
    data = request.json

    # Log the received request data
    app.logger.info(f"Request received with data: {data}")

    if not data or ('text' not in data and 'msg' not in data):
        app.logger.error("No text or message provided")
        return jsonify({"error": "No text or message provided"}), 400

    # Check which field the message was received from
    if 'text' in data:
        text = data['text']
        field_source = 'text'
        level = "warning"
    elif 'msg' in data:  # uptime-kuma
        text = data['msg']
        field_source = 'msg'
        level = "error"
    else:
        return jsonify({"error": "No text field provided"}), 400

    # Process the text in a separate thread
    threading.Thread(target=send_text_to_queue, args=(text, level)).start()

    # Respond immediately that the processing has been queued
    return jsonify({"message": f"Request received from field '{field_source}', processing in progress."}), 200

declare_queues()