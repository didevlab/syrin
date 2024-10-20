import os
import pika
import json
import logging
import shutil
from minio import Minio
from minio.error import S3Error
import sounddevice as sd
import numpy as np
import wave

# Configure INFO level logging
logging.basicConfig(level=logging.INFO)

# Disable pika debug logs, setting to WARNING or higher
logging.getLogger("pika").setLevel(logging.WARNING)

# Load RabbitMQ settings from environment variables
rabbitmq_host = os.getenv('RABBITMQ_HOST', '127.0.0.1')
rabbitmq_port = int(os.getenv('RABBITMQ_PORT', 5672))
rabbitmq_vhost = os.getenv('RABBITMQ_VHOST', '')
rabbitmq_user = os.getenv('RABBITMQ_USER', '')
rabbitmq_pass = os.getenv('RABBITMQ_PASS', '')

# Load delay time between checks from environment variables
rabbitmq_ttl_dlx = int(os.getenv('RABBITMQ_TTL_DLX', 60000))  # 60 seconds TTL (60000 ms)

# Load MinIO settings from environment variables
MINIO_URL = os.getenv('MINIO_URL', '127.0.0.1')
MINIO_PORT = os.getenv('MINIO_PORT', '9000')
MINIO_ROOT_USER = os.getenv('MINIO_ROOT_USER', '')
MINIO_ROOT_PASSWORD = os.getenv('MINIO_ROOT_PASSWORD', '')
MINIO_BUCKET_WORK = os.getenv('MINIO_BUCKET_WORK', 'syrin')

# Connect to MinIO
minio_client = Minio(
    f"{MINIO_URL}:{MINIO_PORT}",
    access_key=MINIO_ROOT_USER,
    secret_key=MINIO_ROOT_PASSWORD,
    secure=False
)

# Function to download a file from MinIO
def download_from_minio(file_name, output_path):
    try:
        minio_client.fget_object(MINIO_BUCKET_WORK, file_name, output_path)
        logging.info(f"File {file_name} successfully downloaded from bucket {MINIO_BUCKET_WORK}.")
        return True
    except S3Error as e:
        logging.error(f"Error downloading file from MinIO: {str(e)}")
        return False

# Function to upload the file to the "reproduced" subfolder or another subfolder
def upload_to_minio(file_name, local_path, subfolder="reproduced"):
    try:
        # Destination path in MinIO (subfolder "reproduced" or another)
        reproduced_file = f"{subfolder}/{file_name}"

        # Upload the file to the desired subfolder in MinIO
        minio_client.fput_object(
            MINIO_BUCKET_WORK,
            reproduced_file,
            local_path
        )
        logging.info(f"File {file_name} successfully uploaded to subfolder '{subfolder}'.")
        return True
    except S3Error as e:
        logging.error(f"Error uploading file {file_name} to subfolder {subfolder}: {str(e)}")
        return False

# Function to delete the local file
def delete_local_file(file_path):
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            logging.info(f"Local file {file_path} successfully deleted.")
        else:
            logging.error(f"Local file {file_path} does not exist to be deleted.")
    except OSError as e:
        logging.error(f"Error deleting local file: {file_path} - {str(e)}")

# Function to delete the original file from MinIO (from the bucket where it was downloaded)
def delete_from_minio(file_name):
    try:
        minio_client.remove_object(MINIO_BUCKET_WORK, file_name)
        logging.info(f"File {file_name} successfully deleted from bucket {MINIO_BUCKET_WORK}.")
    except S3Error as e:
        logging.error(f"Error deleting file {file_name} from bucket: {str(e)}")


# Function to play the audio
def play_audio(output_path):
    try:
        if os.path.exists(output_path):
            logging.info(f"Audio saved at: {output_path}")

            # Load the generated WAV file for playback
            wf = wave.open(output_path, 'rb')

            channels = wf.getnchannels()
            samplerate = wf.getframerate()

            frames = wf.readframes(wf.getnframes())
            audio_data = np.frombuffer(frames, dtype=np.int16)

            # List of devices to ignore
            invalid_devices = [0, 1, 2, 3, 4, 5]

            # Get the list of available audio output devices
            devices = sd.query_devices()

            # Try to play the audio on each available output device, skipping invalid ones
            audio_played = False

            for i, device in enumerate(devices):
                logging.info(f"Ignoring device {i}: {device['name']}")

                if device['max_output_channels'] > 0:
                    try:
                        logging.info(f"Trying to play on device {i}: {device['name']}")

                        # Set the audio device ID
                        sd.default.device = i

                        # Play the audio on the specified device
                        sd.play(audio_data, samplerate=samplerate, device=i)

                        # Wait until the audio finishes playing
                        sd.wait()

                        audio_played = True
                        logging.info(f"Audio successfully played on device {i}: {device['name']}")
                        break  # Exit the loop after the first successful playback
                    except Exception as e:
                        logging.error(f"Error playing on device {i}: {device['name']}, error: {e}")

            if audio_played:
                logging.info("Text successfully converted and played.")
                return True
            else:
                logging.error("Failed to play audio on any output device.")
                return False
        else:
            logging.error("Error finding the audio file for playback.")
            return False
    except Exception as e:
        logging.error(f"Error playing audio: {str(e)}")
        return False

# Function to download, play, upload, and delete the local and bucket file
def process_audio(file_name):
    try:
        output_path = f"/tmp/{file_name}"

        # Download the audio file from MinIO
        if download_from_minio(file_name, output_path):
            # Play the audio
            if play_audio(output_path):
                # Upload to the "reproduced" subfolder
                if upload_to_minio(file_name, output_path, "reproduced"):
                    # Delete the local file after successful upload
                    delete_local_file(output_path)
                    # Delete the original file from MinIO after successful upload
                    delete_from_minio(file_name)
                else:
                    logging.error(f"Failed to upload file {file_name} to MinIO.")
            else:
                logging.error(f"Failed to play audio {file_name}.")
                delete_local_file(output_path)  # Delete the local file even if playback fails
        else:
            logging.error(f"Failed to download file {file_name} from MinIO.")
    except Exception as e:
        logging.error(f"Error processing audio {file_name}: {str(e)}")

def publish_to_reproduced_queue(channel, message):
    try:
        queue = '004_notification_process_audio_reproduced'
        channel.queue_declare(queue=queue, durable=True)
        channel.basic_publish(
            exchange='',
            routing_key=queue,
            body=json.dumps(message, ensure_ascii=False),
            properties=pika.BasicProperties(delivery_mode=2)
        )
        logging.info(f"Message published to queue {queue}: {message}")
    except Exception as e:
        logging.error(f"Error publishing message to queue {queue}: {str(e)}")

def publish_to_reprocess_queue(channel, message):
    try:
        # Declare the reprocessing queue with TTL and DLX
        channel.queue_declare(
            queue='003_notification_reprocess_play_audio',
            durable=True,
            arguments={
                'x-message-ttl': rabbitmq_ttl_dlx,  # TTL configurable via environment variable
                'x-dead-letter-exchange': '',  # Default DLX to route to another queue
                'x-dead-letter-routing-key': '003_notification_process_play_audio'  # Queue where the message will be moved
            }
        )
        # Publish the message to the reprocessing queue
        channel.basic_publish(
            exchange='',
            routing_key='003_notification_reprocess_play_audio',
            body=json.dumps(message, ensure_ascii=False),
            properties=pika.BasicProperties(delivery_mode=2)
        )
        logging.info(f"Message sent to reprocessing queue: {message['filename']}")
    except Exception as e:
        logging.error(f"Error sending message to reprocessing queue: {str(e)}")

def connect_to_rabbitmq():
    try:
        # Set credentials and connection parameters
        credentials = pika.PlainCredentials(rabbitmq_user, rabbitmq_pass)
        
        # Set client properties, including connection name
        client_properties = {
            "connection_name": "Syrin Speak Audio Agent"
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

def on_message_callback(channel, method_frame, header_frame, body):
    try:
        message = json.loads(body.decode())
        logging.info(f"Message received from queue 003_notification_process_play_audio: File: {message['filename']}")

        # Process the audio: download, play, upload, and delete locally
        process_audio(message['filename'])

        # Publish the item to queue process_notification_reproduced
        publish_to_reproduced_queue(channel, message)

        # Acknowledge message removal from queue 003_notification_process_play_audio
        channel.basic_ack(method_frame.delivery_tag)
    except Exception as e:
        logging.error(f"Error in callback while processing message: {str(e)}")
        channel.basic_ack(method_frame.delivery_tag)

def consume_messages():
    try:
        connection = connect_to_rabbitmq()
        if connection is None:
            logging.error("Failed to connect to RabbitMQ. Shutting down the application.")
            return

        channel = connection.channel()

        # Declare queues to ensure they exist
        queues_to_declare = [
            '003_notification_process_play_audio',
            '003_notification_reprocess_play_audio',
            '004_notification_process_audio_reproduced'
        ]

        for queue in queues_to_declare:
            channel.queue_declare(
                queue=queue, 
                durable=True,
                arguments={
                    'x-message-ttl': rabbitmq_ttl_dlx,
                    'x-dead-letter-exchange': '',
                    'x-dead-letter-routing-key': '003_notification_process_play_audio'
                } if queue == '003_notification_reprocess_play_audio' else None
            )
            logging.info(f"Queue '{queue}' verified or created.")

        # Register the callback to consume messages
        channel.basic_consume(queue='003_notification_process_play_audio', on_message_callback=on_message_callback)

        logging.info("Waiting for messages...")
        
        # Start consuming messages
        channel.start_consuming()
    except Exception as e:
        logging.error(f"Error consuming messages: {str(e)}")
    finally:
        if connection and connection.is_open:
            connection.close()
            logging.info("RabbitMQ connection closed.")

if __name__ == "__main__":
    try:
        logging.info("Syrin Speak Audio - started \o/")
        consume_messages()
    except Exception as e:
        logging.error(f"Error running the application: {str(e)}")
