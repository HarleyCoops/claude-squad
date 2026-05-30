FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libopencv-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# Install the package
RUN pip install -e .

# Create required directories
RUN mkdir -p /data/content_inbox /data/content_processed /data/content_failed /data/temp

# Set environment variables
ENV WATCH_DIRECTORY=/data/content_inbox
ENV PROCESSED_DIRECTORY=/data/content_processed
ENV FAILED_DIRECTORY=/data/content_failed
ENV TEMP_DIRECTORY=/data/temp
ENV PYTHONUNBUFFERED=1

# Expose volume for data
VOLUME ["/data"]

# Run the application
CMD ["social-media-pipeline"]

