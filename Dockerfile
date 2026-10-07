FROM python:3.11-slim

WORKDIR /app

# Prevent Python from writing .pyc files and enable unbuffered logging
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Ensure certificates directory exists
RUN mkdir -p generated_certificates

EXPOSE 8000

# Default command (Web API)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
