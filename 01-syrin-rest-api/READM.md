pip install pika flask


# SYRIN REST API

This project is a Flask-based REST API that integrates with RabbitMQ to process and send text-based notifications to a message queue. The API receives text input via HTTP POST requests and then sends the text to a RabbitMQ queue, which can be processed further downstream.

## Features

- **Text-to-Queue Processing**: The API accepts a JSON payload with text or message data, then pushes it to a RabbitMQ queue for further processing.
- **Queue Declaration**: At startup, the necessary RabbitMQ queues are declared to ensure they exist before processing.
- **Asynchronous Processing**: The text message processing is handled in a separate thread to ensure non-blocking operations for the API.
- **Environment-Based Configuration**: RabbitMQ credentials and connection details are loaded from environment variables.

## How it Works

### Endpoints

- **POST /api/text-to-speech**

  This endpoint processes incoming requests containing text or message data and sends the data to a RabbitMQ queue. Depending on the type of input, the message is routed to either the `000_notification_warning` or `000_notification_error` queue.

#### Example Request

```bash
curl -X POST http://localhost:5121/api/text-to-speech \
    -H "Content-Type: application/json" \
    -d '{"text": "This is a warning message."}'
```

#### Example Response

```json
{
  "message": "Request received from field 'text', processing in progress."
}
```

### RabbitMQ Queues

- `000_notification_warning`: Queue for messages tagged with "warning" level.
- `000_notification_error`: Queue for messages tagged with "error" level.

### Environment Variables

The RabbitMQ connection details are configured through the following environment variables:

- `RABBITMQ_HOST`: The hostname or IP of the RabbitMQ server.
- `RABBITMQ_PORT`: The port RabbitMQ is listening on (default: 5672).
- `RABBITMQ_VHOST`: The virtual host used in RabbitMQ.
- `RABBITMQ_USER`: The RabbitMQ username.
- `RABBITMQ_PASS`: The RabbitMQ password.

### Workflow

1. **Queue Declaration**: When the Flask app starts, it declares the required queues (`000_notification_warning` and `000_notification_error`) to ensure they are available for message publishing.
2. **Message Handling**: A POST request is made to the `/api/text-to-speech` endpoint with JSON data containing either a `text` or `msg` field. Based on the field and content, the message is routed to the appropriate queue in RabbitMQ.
3. **Asynchronous Processing**: The message is sent to RabbitMQ in a separate thread, ensuring that the API responds immediately, and the text is processed in the background.
4. **Queue Publishing**: The message is published to RabbitMQ with persistence enabled (delivery mode 2), ensuring that the message is not lost if RabbitMQ restarts.

## Running the Application

To run the application, follow these steps:

1. **Set up RabbitMQ**: Make sure you have RabbitMQ installed and running. You can use a Docker container for RabbitMQ:

    ```bash
    docker run -d --name rabbitmq -p 5672:5672 -p 15672:15672 rabbitmq:management
    ```

2. **Clone the repository** and navigate to the project directory:

    ```bash
    git clone <repository_url>
    cd <project_directory>
    ```

3. **Install dependencies**:

    ```bash
    pip install -r requirements.txt
    ```

4. **Run the Flask API**:

    ```bash
    python app.py
    ```

5. **Send requests**: Use tools like `curl` or Postman to send a POST request to the `/api/text-to-speech` endpoint.

## Docker Support

You can also build and run the application using Docker. To do this:

1. **Build the Docker image**:

    ```bash
    docker build -t didevlab/poc:syrin_restapi-1.0.0 .
    ```

2. **Run the Docker container**:

    ```bash
    docker run -d -p 5121:5121 --env-file .env didevlab/poc:syrin_restapi-1.0.0
    ```

## Technologies Used

- **Flask**: Web framework for creating the REST API.
- **RabbitMQ**: Message broker used for queueing and processing text messages.
- **Pika**: Python library for interacting with RabbitMQ.
- **Threading**: To handle message sending asynchronously.

## License

This project is licensed under the MIT License.
