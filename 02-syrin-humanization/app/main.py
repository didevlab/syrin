import os
import pika
import json
import logging
import requests

# Configure INFO level logging
logging.basicConfig(level=logging.INFO)

# Disable pika debug logs, setting them to WARNING or higher
logging.getLogger("pika").setLevel(logging.WARNING)

# Load RabbitMQ settings from environment variables
rabbitmq_host = os.getenv('RABBITMQ_HOST', '')
rabbitmq_port = int(os.getenv('RABBITMQ_PORT', 5672))
rabbitmq_vhost = os.getenv('RABBITMQ_VHOST', '')
rabbitmq_user = os.getenv('RABBITMQ_USER', '')
rabbitmq_pass = os.getenv('RABBITMQ_PASS', '')
rabbitmq_ttl_dlx = int(os.getenv('RABBITMQ_TTL_DLX', 60000))  # 60 seconds TTL (60000 ms)

# Load Ollama AI settings
OLLAMA_HOSTNAME = os.getenv('OLLAMA_HOSTNAME', '127.0.0.1:11434')
OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'llama3.1')

# Load Ollama AI prompts
PROMPT_ERROR = os.getenv('PROMPT_ERROR', 'I will give you a text where I want you to inform me in a professional and direct manner what happened. Your information should request a technical team to get involved to solve the issue briefly, and your response should never exceed 200 characters. Here is the text:')
PROMPT_GENERIC = os.getenv('PROMPT_GENERIC', 'I will give you a text, where I want you to use humor. The text will be in Brazilian Portuguese, and your response must be exactly and only one sentence in Portuguese. Your response should be in an informative or directive tone so I can take action based on the content of the following text:')

def connect_to_rabbitmq():
    try:
        # Set the credentials and connection parameters
        credentials = pika.PlainCredentials(rabbitmq_user, rabbitmq_pass)
        
        # Set client properties, including connection name
        client_properties = {
            "connection_name": "Syrin Text Humanized Agent"
        }
        
        parameters = pika.ConnectionParameters(
            host=rabbitmq_host,
            port=rabbitmq_port,
            virtual_host=rabbitmq_vhost,
            credentials=credentials,
            client_properties=client_properties  # Pass the connection name here
        )
        
        return pika.BlockingConnection(parameters)
    except Exception as e:
        logging.error(f"Error connecting to RabbitMQ: {str(e)}")
        return None

def delete_queue_if_exists(channel, queue_name):
    try:
        # Attempt to delete the existing queue
        channel.queue_delete(queue=queue_name)
        logging.info(f"Queue '{queue_name}' deleted successfully.")
    except pika.exceptions.ChannelClosedByBroker as e:
        if e.reply_code == 404:
            logging.info(f"Queue '{queue_name}' does not exist. No action needed.")
        else:
            logging.error(f"Error deleting queue '{queue_name}': {str(e)}")
            raise

def requestOllama(text, level):
    url = f"http://{OLLAMA_HOSTNAME}/api/generate"

    if level == "error":
        prompt = f"{PROMPT_ERROR} {text}"
    else:
        prompt = f"{PROMPT_GENERIC} {text}"

    payload = {
        "model": OLLAMA_MODEL,
        "stream": False,
        "prompt": prompt
    }

    try:
        response = requests.post(url, json=payload, timeout=120)
        response.raise_for_status()
        response_data = response.json()

        return response_data.get("response")
    except requests.RequestException as e:
        logging.error(f"Error in request to Ollama: {str(e)}")
        return ""

def declare_reprocess_queue(channel):
    try:
        # Delete the queue if it already exists to avoid parameter conflicts
        delete_queue_if_exists(channel, '001_notification_reprocess_humanized')
        
        # Declare the queue with TTL and DLX
        channel.queue_declare(
            queue='001_notification_reprocess_humanized',
            durable=True,
            arguments={
                'x-message-ttl': rabbitmq_ttl_dlx,  # 60 seconds TTL (60000 ms)
                'x-dead-letter-exchange': '',  # Default DLX for routing to another queue
                'x-dead-letter-routing-key': '001_notification_process_humanized'  # Queue to move the message to
            }
        )
        logging.info(f"Queue '001_notification_reprocess_humanized' checked or created with TTL of {rabbitmq_ttl_dlx} ms.")
    except Exception as e:
        logging.error(f"Error declaring the reprocessing queue: {str(e)}")

def reprocess_message(channel, message):
    try:
        # Ensure the queue was declared correctly with TTL and DLX arguments
        declare_reprocess_queue(channel)
        
        # Publish the message to the queue
        channel.basic_publish(
            exchange='',
            routing_key='001_notification_reprocess_humanized',
            body=json.dumps(message, ensure_ascii=False),  # Allow special characters in JSON
            properties=pika.BasicProperties(delivery_mode=2)  # Persist the message
        )
        
        logging.info(f"Message sent to the reprocessing queue: {message['text']}")
    except Exception as e:
        logging.error(f"Error reprocessing the message: {str(e)}")

def send_to_humanized_queue(channel, text_humanized, original_message):
    try:
        # Ensure the '001_notification_process_humanized' queue exists
        channel.queue_declare(queue='001_notification_process_humanized', durable=True)

        # Send the humanized text to the queue
        message = {
            'original_text': original_message['text'],
            'level': original_message['level'],
            'humanized_text': text_humanized
        }
        
        channel.basic_publish(
            exchange='',
            routing_key='001_notification_process_humanized',
            body=json.dumps(message, ensure_ascii=False),  # Allow special characters in JSON
            properties=pika.BasicProperties(delivery_mode=2)  # Persist the message
        )
        
        logging.info(f"Humanized message sent to '001_notification_process_humanized' queue: {message}")
    except Exception as e:
        logging.error(f"Error sending message to the humanized queue: {str(e)}")

def on_message_callback(channel, method_frame, header_frame, body):
    try:
        message = json.loads(body.decode())

        logging.info(f"Message received from queue {method_frame.routing_key}: {message['text']}, {message['level']}")
        text_humanized = requestOllama(message['text'], message['level'])

        if text_humanized:
            logging.info(f"Humanized message: {text_humanized}")
            send_to_humanized_queue(channel, text_humanized, message)
        else:
            logging.error(f"Failed to humanize the message: {message['text']}")
            reprocess_message(channel, message)
        
        # Acknowledge that the message was successfully processed
        channel.basic_ack(method_frame.delivery_tag)
    except Exception as e:
        logging.error(f"Error in callback processing message: {str(e)}")
        channel.basic_ack(method_frame.delivery_tag)

def consume_messages():
    try:
        connection = connect_to_rabbitmq()
        if connection is None:
            logging.error("Connection to RabbitMQ failed. Exiting the application.")
            return

        channel = connection.channel()

        # Declare all queues to ensure they exist before consuming
        queues_to_declare = [
            '000_notification_error',
            '000_notification_warning',
            '001_notification_process_humanized'
        ]

        for queue in queues_to_declare:
            channel.queue_declare(queue=queue, durable=True)
            logging.info(f"Queue '{queue}' checked or created.")

        # Check or declare the reprocessing queue with TTL and DLX
        declare_reprocess_queue(channel)

        # Register callback for error and warning queues
        channel.basic_consume(queue='000_notification_error', on_message_callback=on_message_callback)
        channel.basic_consume(queue='000_notification_warning', on_message_callback=on_message_callback)

        logging.info("Waiting for messages...")

        # Start consuming messages
        channel.start_consuming()
    except Exception as e:
        logging.error(f"Error in message consumption: {str(e)}")
    finally:
        if connection and connection.is_open:
            connection.close()
            logging.info("Connection to RabbitMQ closed.")

if __name__ == "__main__":
    try:
        logging.info("Syrin text humanized - started \o/")
        consume_messages()
    except Exception as e:
        logging.error(f"Error running the application: {str(e)}")
