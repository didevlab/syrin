pip install pika 
pip install minio
pip install TTS==0.22.0

# Syrin TTS Make Audio

This repository contains a Python application that consumes messages from a RabbitMQ queue, processes text messages using the Coqui TTS library, generates speech audio files, and uploads these files to a MinIO storage server. If any step fails, the message is requeued for reprocessing.

## Features

- **Text-to-Speech (TTS)**: Uses Coqui TTS to generate speech audio from text messages.
- **RabbitMQ integration**: Consumes messages from RabbitMQ, processes them, and publishes new messages after generating the audio.
- **MinIO integration**: Uploads generated `.wav` audio files to a MinIO bucket.
- **Reprocessing mechanism**: Messages that fail to be processed are sent to a reprocessing queue.

## How It Works

1. **Consuming Messages**: The application connects to RabbitMQ and consumes messages from the `001_notification_process_humanized` queue. These messages contain text that needs to be transformed into audio.
   
2. **Generating Audio**: The application uses the Coqui TTS model `your_tts` to convert the text into speech. The resulting audio is saved as a `.wav` file with a timestamp in its filename.
   
3. **Uploading Audio**: After generating the audio, the `.wav` file is uploaded to a MinIO bucket specified by environment variables.
   
4. **Publishing Messages**: Once the audio is uploaded, the application publishes the message, with an updated filename, to the `003_notification_process_play_audio` queue.

5. **Reprocessing Failed Messages**: If the audio generation or file upload fails, the message is sent to the `002_notification_reprocess_make_audio` queue for retrying later.

## Environment Variables

The application uses the following environment variables for configuration:

- `RABBITMQ_HOST`: The RabbitMQ host (default: `127.0.0.1`)
- `RABBITMQ_PORT`: The RabbitMQ port (default: `5672`)
- `RABBITMQ_VHOST`: The RabbitMQ virtual host (default: ` `)
- `RABBITMQ_USER`: The RabbitMQ user (default: ` `)
- `RABBITMQ_PASS`: The RabbitMQ password (default: ` `)
- `RABBITMQ_TTL_DLX`: TTL (time-to-live) in milliseconds for messages in the reprocess queue (default: `60000` ms)
- `MINIO_URL`: The MinIO URL (default: `127.0.0.1`)
- `MINIO_PORT`: The MinIO port (default: `9000`)
- `MINIO_ROOT_USER`: The MinIO root user (default: ` `)
- `MINIO_ROOT_PASSWORD`: The MinIO root password (default: ` `)
- `MINIO_BUCKET_WORK`: The MinIO bucket where audio files are uploaded (default: `syrin`)

## File Structure

- `app/`: Contains the Python code for the application.
- `requirements.txt`: Lists the dependencies needed for the Python environment.

## Running the Application

To run the application, follow these steps:

1. **Install Dependencies**: Make sure you have Python 3.9 and pip installed. Install the required dependencies with:
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

2. **Set Up RabbitMQ and MinIO**: Ensure that RabbitMQ and MinIO services are running and properly configured.

3. **Run the Application**: Execute the Python application:
   ```bash
   python main.py
   ```

4. **Docker**: You can build and run the application using Docker as well. Use the following commands to build and run:
   ```bash
   docker build -t didevlab/poc:syrin_make_audio_tts-1.0.0 .
   docker run -d --env-file .env didevlab/poc:syrin_make_audio_tts-1.0.0
   ```

## Error Handling and Reprocessing

- If there is an issue generating the audio file or uploading it to MinIO, the message is sent to a reprocessing queue with a TTL of 60 seconds.
- After the TTL expires, the message is moved back to the `001_notification_process_humanized` queue for reprocessing.

## Requirements

- Python 3.9+
- RabbitMQ
- MinIO
- Coqui TTS Library
- Dependencies listed in `requirements.txt`

## Logs

The application uses Python's `logging` library to log important events like successful uploads, message publications, and errors.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
