FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install redis-server so Celery can run self-contained
RUN apt-get update && \
    apt-get install -y --no-install-recommends redis-server bash && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY . .

# Ensure storage directory exists and start script is executable
RUN mkdir -p generated_certificates && chmod +x start.sh

EXPOSE 8000

CMD ["./start.sh"]
