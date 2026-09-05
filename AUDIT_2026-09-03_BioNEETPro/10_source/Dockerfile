FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy dependencies
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY app.py app.py

# Expose backend port
EXPOSE 5000

# Set environment variables
ENV FLASK_DEBUG=false
ENV PORT=5000

# Run Flask application
CMD ["python", "app.py"]
