FROM python:3.11-slim-bookworm

# Install system dependencies: FFmpeg and build essentials
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    gcc \
    g++ \
    make \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -U pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Expose port for Koyeb web health checks
EXPOSE 8080

# Start bot
CMD ["python3", "main.py"]
