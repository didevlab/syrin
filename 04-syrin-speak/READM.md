# Syrin Speak Audio Agent

## Description

This project implements an audio agent to process messages received from a RabbitMQ queue, which include information about audio files stored in MinIO. The agent performs the following tasks:

1. Downloads the audio file from the MinIO bucket.
2. Plays the audio on available audio output devices.
3. Uploads the reproduced audio file to a subfolder in MinIO.
4. Deletes the original file from MinIO and also the local file after processing.
5. Publishes a message indicating the successful processing to another RabbitMQ queue.

## Features

- **RabbitMQ**: The agent connects to a RabbitMQ queue, receives messages, processes the indicated audio files, and publishes the results to other queues.
- **MinIO**: The agent interacts with MinIO to download and upload audio files.
- **Audio Playback**: Attempts to play the downloaded audio on all available audio output devices until a compatible device is found.
- **Reprocessing Queue**: If audio playback fails, the file is sent to a reprocessing queue with a configurable TTL (Time To Live).

## Requirements

- **Python 3.x**
- **Python Libraries**:
  - `pika` (for RabbitMQ communication)
  - `minio` (for interacting with MinIO)
  - `sounddevice` (for audio playback)
  - `numpy` (for audio data processing)
  - `wave` (for reading WAV audio files)
  
  You can install the dependencies using the following command:
  
  ```bash
  pip install pika minio sounddevice numpy wave
  ```

## Configuration

Settings are loaded from environment variables. Here is a list of variables you need to define:

- **RabbitMQ**:
  - `RABBITMQ_HOST`: RabbitMQ IP address or hostname (default: `127.0.0.1`)
  - `RABBITMQ_PORT`: RabbitMQ port (default: `5672`)
  - `RABBITMQ_VHOST`: RabbitMQ virtual host (default: empty)
  - `RABBITMQ_USER`: RabbitMQ user
  - `RABBITMQ_PASS`: RabbitMQ password
  - `RABBITMQ_TTL_DLX`: TTL time for messages in milliseconds (default: `60000`)

- **MinIO**:
  - `MINIO_URL`: MinIO IP address or hostname (default: `127.0.0.1`)
  - `MINIO_PORT`: MinIO port (default: `9000`)
  - `MINIO_ROOT_USER`: MinIO access key
  - `MINIO_ROOT_PASSWORD`: MinIO secret key
  - `MINIO_BUCKET_WORK`: MinIO bucket name (default: `syrin`)

## How to Run

1. Ensure that you have the environment variables configured correctly.
2. Run the main Python script:

```bash
python your_script_name.py
```

The agent will start consuming messages from the `003_notification_process_play_audio` queue. For each message:

- The audio file will be downloaded from MinIO.
- The audio will be played on the first valid audio output device found.
- The file will be moved to the `reproduced` subfolder in MinIO.
- The local file will be deleted after processing.

## Code Structure

- **RabbitMQ Connection**: The `connect_to_rabbitmq` function manages the connection to RabbitMQ and returns a valid connection to consume messages.
- **Message Processing**: The `on_message_callback` function is the main callback that processes the received messages. It handles the flow of downloading, playing, and uploading the file.
- **Audio Playback**: The `play_audio` function attempts to play the audio file on various available audio devices until successful playback is achieved.
- **MinIO Interaction**: The functions `download_from_minio`, `upload_to_minio`, and `delete_from_minio` handle downloading, uploading, and deleting files in MinIO.

## Reprocessing Queue

If the audio cannot be played, the message is sent to the `003_notification_reprocess_play_audio` queue, which has a configurable TTL. After the TTL expires, the message will be rerouted to the original queue for another processing attempt.

## Logging

The logging system is configured to track progress and log any errors encountered during processing. All logs are displayed in the console. The log level for `pika` has been set to `WARNING` to avoid unnecessary noise.

## Contribution

If you would like to contribute to this project, please follow these steps:

1. Fork this repository.
2. Create a branch for your new feature (`git checkout -b feature/MyFeature`).
3. Commit your changes (`git commit -m 'Add MyFeature'`).
4. Push to the branch (`git push origin feature/MyFeature`).
5. Open a Pull Request.

## License

This project is licensed under the [MIT License](LICENSE).

## Installation Procedure

To install and configure the `syrin-speak` service, follow these steps:

### Install Required Python Libraries

```bash
sudo pip install numpy
sudo pip install pika
sudo pip install minio
sudo pip install sounddevice
```

### Copy and Configure the Service

1. Copy the Python script to the appropriate location:
    ```bash
    sudo cp ./service/syrin-speak.py /usr/local/bin/syrin-speak.py
    ```

2. Make the script executable:
    ```bash
    sudo chmod +x /usr/local/bin/syrin-speak.py
    ```

3. Copy the service file to the systemd directory:
    ```bash
    sudo cp ./service/syrin-speak.service /etc/systemd/system/syrin-speak.service
    ```

4. Add the current user to the audio group to allow audio playback:
    ```bash
    sudo usermod -aG audio $USER
    ```

5. Reload the systemd daemon:
    ```bash
    sudo systemctl daemon-reload
    ```

6. Enable the service to start at boot:
    ```bash
    sudo systemctl enable syrin-speak.service
    ```

7. Start the service:
    ```bash
    sudo systemctl start syrin-speak.service
    ```

8. Check the status of the service:
    ```bash
    sudo systemctl status syrin-speak.service
    ```

9. View the service logs:
    ```bash
    journalctl -u syrin-speak.service -f
    ```

### Alternative Installation with Virtual Environment

1. Navigate to the virtual environment directory:
    ```bash
    cd /myenv
    ```

2. Create the `syrin-speak.py` script:
    ```bash
    touch syrin-speak.py
    ```

3. Copy the content of the script and paste it into `syrin-speak.py`:
    ```bash
    vim syrin-speak.py
    ```

4. Install additional dependencies for audio:
    ```bash
    sudo apt install portaudio19-dev python3-pyaudio
    ```

5. Activate the virtual environment:
    ```bash
    sudo source myenv/bin/activate
    ```

6. Start the service as a user service:
    ```bash
    systemctl --user start syrin-speak.service
    ```

7. Check the status of the user service:
    ```bash
    systemctl --user status syrin-speak.service
    ```

8. View the logs for the user service:
    ```bash
    journalctl --user-unit syrin-speak.service -f
    ```
