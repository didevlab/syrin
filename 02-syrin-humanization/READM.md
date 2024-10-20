pip install pika requests


# Syrin Text Humanized Agent

This project is a Python application that processes messages from RabbitMQ queues, interacts with an AI service (Ollama), and transforms text into a humanized format. The humanized text is then published to a different RabbitMQ queue for further processing. The application handles error and warning messages, reprocesses failed messages, and ensures message persistence through RabbitMQ's durable queues.

## Features

- **RabbitMQ integration:** Consumes messages from specific RabbitMQ queues and publishes humanized responses back to other queues.
- **Ollama AI interaction:** Uses the Ollama AI model to generate humanized text based on the message content.
- **Reprocessing capability:** If a message cannot be humanized, it is re-routed to a special reprocessing queue for retrying.
- **Customizable:** The prompts sent to the AI can be customized through environment variables.

## Environment Variables

This application relies on the following environment variables for configuration:

- `RABBITMQ_HOST`: The RabbitMQ server hostname (default: `127.0.0.1`)
- `RABBITMQ_PORT`: The RabbitMQ server port (default: `5672`)
- `RABBITMQ_VHOST`: The RabbitMQ virtual host to connect to (default: ` `)
- `RABBITMQ_USER`: The RabbitMQ username (default: ` `)
- `RABBITMQ_PASS`: The RabbitMQ password (default: ` `)
- `RABBITMQ_TTL_DLX`: Time-to-live (TTL) in milliseconds for messages in the reprocessing queue (default: `60000` ms)
- `OLLAMA_HOSTNAME`: The hostname of the Ollama AI service (default: `127.0.0.1:11434`)
- `OLLAMA_MODEL`: The Ollama AI model to use (default: `llama3.1`)
- `PROMPT_ERROR`: Custom prompt for handling error messages.
- `PROMPT_GENERIC`: Custom prompt for handling general messages in a humorous tone.

## How It Works

1. **RabbitMQ Connection:** The application connects to a RabbitMQ instance using credentials and connection parameters defined by environment variables.
   
2. **Queue Declaration:** Several RabbitMQ queues are declared to ensure they exist before the application starts consuming messages:
   - `000_notification_error`: For error messages.
   - `000_notification_warning`: For warning messages.
   - `001_notification_process_humanized`: For humanized messages.

3. **Message Processing:**
   - The application consumes messages from the `000_notification_error` and `000_notification_warning` queues.
   - It sends the message content to Ollama AI for humanization using a pre-defined prompt.
   - The humanized response is then sent to the `001_notification_process_humanized` queue.

4. **Reprocessing Failed Messages:** If the AI fails to generate a response, the message is sent to a reprocessing queue (`001_notification_reprocess_humanized`), where it will be retried after a specified TTL (60 seconds by default).

5. **Acknowledgment and Persistence:**
   - After successful processing, the message is acknowledged to RabbitMQ using `basic_ack`.
   - All messages are published to RabbitMQ queues with persistence (`delivery_mode=2`), ensuring they are saved even if RabbitMQ restarts.

## Running the Application

### Prerequisites

- Python 3.9 or higher
- RabbitMQ instance running with necessary queues and credentials.
- An Ollama AI service accessible at the hostname defined in `OLLAMA_HOSTNAME`.

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/your-repo/syrin-text-humanized.git
   cd syrin-text-humanized
   ```

2. Install the required Python packages:
   ```bash
   pip install -r requirements.txt
   ```

### Running the Application

To run the application, simply execute:

```bash
python app.py
```

Make sure the environment variables are set up either in your environment or in a `.env` file.

### Docker

You can also build and run the application using Docker:

1. Build the Docker image:
   ```bash
   docker build -t didevlab/poc:syrin_humanization-1.0.0 .
   ```

2. Run the Docker container:
   ```bash
   docker run -d --env-file .env didevlab/poc:syrin_humanization-1.0.0
   ```

## Logging

The application uses Python's `logging` library to log messages. Logs are displayed with `INFO` level by default, but logs from the `pika` library (RabbitMQ) are set to `WARNING` level or higher to reduce verbosity.

## Error Handling

- If the connection to RabbitMQ fails, the application logs the error and stops execution.
- If an error occurs during message processing, the application logs the error and acknowledges the message to avoid blocking the queue.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
