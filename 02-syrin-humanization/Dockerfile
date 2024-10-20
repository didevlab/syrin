# Use a base image of Python
FROM python:3.9-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the necessary files to the working directory
COPY requirements.txt .
COPY ./app/ .

# Install Python dependencies
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 80

# docker build -t didevlab/poc:syrin_humanization-1.0.0 .
