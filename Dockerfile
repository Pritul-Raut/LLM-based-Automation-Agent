# Use Python slim image with Python 3.10 as a base image
FROM python:3.10-slim-bookworm

# Install Node.js, npm, and other necessary dependencies
RUN apt-get update && apt-get install -y \
    nodejs \
    npm \
    curl \
    ca-certificates \
    python3-pip \
    git \
    ffmpeg \
    sqlite3 \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r /app/requirements.txt

# Download the latest UVicorn installer
ADD https://astral.sh/uv/install.sh /uv-installer.sh

# Run the installer and then remove it
RUN sh /uv-installer.sh && rm /uv-installer.sh

# Ensure the installed binary is on the PATH
ENV PATH="/root/.local/bin/:$PATH"

# Set the working directory in the container
WORKDIR /app

# Copy the application code into the container
COPY app.py /app

# Create necessary directories
RUN mkdir -p /data

# Expose the application's port
EXPOSE 8000

# Command to run the application
CMD ["uv", "run", "app.py"]
