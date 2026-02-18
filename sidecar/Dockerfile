# sidecar/Dockerfile
FROM python:3.11-slim

# Install netcat/procps if you plan on using shell-based connection checks
RUN apt-get update && apt-get install -y netcat-openbsd procps && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install docker SDK to talk to the socket and requests for your API
RUN pip install --no-cache-dir docker requests

COPY . .

# Default environment variables
ENV TICK_RATE=30
ENV IDLE_THRESHOLD=900
ENV GAME_TYPE=generic

CMD ["python", "main.py"]