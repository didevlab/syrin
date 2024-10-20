
# ![SYRIN Logo](./Syrin.png)

# SYRIN - Humanized Audio Notification System

SYRIN is a set of applications designed to transform text messages into humanized audio alerts. The system integrates RabbitMQ and MinIO to process and distribute these messages in queues, ensuring personalized and fast notifications that can be played in real-time on audio devices. SYRIN was designed to improve the efficiency of monitoring teams by providing a more engaging experience, transforming technical alerts into humanized messages.

## Project Components

### 1. SYRIN REST API

A Flask-based REST API that receives text messages and sends them to RabbitMQ queues. This API offers endpoints for receiving input data and distributing it to notification queues, with asynchronous processing and support for different priority levels.

**Key Features**:
- Text message processing for RabbitMQ queues.
- Reprocessing queue for handling failures.
- Environment variable configuration for RabbitMQ connection details and credentials.

**Request Example**:
```bash
curl -X POST http://localhost:5121/api/text-to-speech     -H "Content-Type: application/json"     -d '{"text": "This is a warning message."}'
```

### 2. SYRIN Humanized Text Agent

This component is responsible for transforming text messages into more humanized formats using the Ollama AI model. It consumes messages from RabbitMQ queues, processes the text, and returns a more natural and fluid version of those messages to a new queue.

**Key Features**:
- Integration with Ollama AI for message humanization.
- Reprocessing of messages in case of failure.
- Customizable prompts for humanization through environment variables.

### 3. SYRIN TTS Make Audio

This component generates audio files from text messages using the Coqui TTS library. The resulting audio files are uploaded to MinIO, and the messages are forwarded to new queues for playback.

**Key Features**:
- Audio generation from text using Coqui TTS.
- Upload of `.wav` files to a MinIO bucket.
- Reprocessing mechanism in case of audio processing failure.

### 4. SYRIN Speak Audio Agent

SYRIN Speak is responsible for consuming messages from queues that indicate the location of audio files in MinIO. It downloads the files, plays them on audio devices, and then moves the processed files to a subfolder in MinIO.

**Key Features**:
- Audio playback from `.wav` files.
- MinIO interaction for downloading/uploading files.
- Publication of success or failure messages to other RabbitMQ queues.

## How It Works

1. **Message Reception**: Messages are received via REST API and forwarded to RabbitMQ.
2. **Humanization**: The text messages go through the humanization agent, which generates a more natural version of the text using AI.
3. **Audio Generation**: The humanized text is converted into audio using Coqui TTS.
4. **Audio Playback**: The playback agent downloads the audio files from MinIO and plays them on sound devices.
5. **File Management**: After playback, the audio files are moved to a "reproduced" subfolder in MinIO.

## Technologies Used

- **Flask**: For creating the REST API.
- **RabbitMQ**: For processing and distributing messages.
- **Pika**: Python library for RabbitMQ integration.
- **Ollama AI**: AI model for text humanization.
- **Coqui TTS**: For converting text into audio.
- **MinIO**: For storing generated audio files.
- **sounddevice** and **numpy**: For audio playback.

## Execution

### Requirements

- Python 3.x
- RabbitMQ
- MinIO
- Docker (optional)

### Instructions

1. Clone the repository and navigate to the project directory.
   ```bash
   git clone https://github.com/didevlab/syrin
   cd syrin
   ```

2. Install the dependencies.
   ```bash
   pip install -r requirements.txt
   ```

3. Configure your environment variables as needed (RabbitMQ, MinIO, Ollama).

4. Run each component individually.
   ```bash
   python app.py  # For the REST API, Humanized Text Agent, or Make Audio Agent
   ```

### Docker

You can use Docker to simplify the execution:
```bash
docker build -t syrin:latest .
docker run -p 5121:5121 syrin:latest
```

## License

This project is licensed under the MIT License.
