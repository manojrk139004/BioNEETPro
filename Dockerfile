FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy dependencies
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Backend source modules & frontend assets
COPY app.py tutor_engine.py retrieval_engine.py learner_model.py mcq_engine.py firestore_store.py adaptive_tutor.py nlp_pipeline.py *.py ./
COPY *.html ./
COPY *.js ./
COPY *.css ./

# Runtime data
COPY data ./data
COPY scripts ./scripts
COPY datasets ./datasets

# NCERT textbook PDFs required by /api/textbook/pdf/*
COPY Textbook ./Textbook

# Cloud platforms provide PORT dynamically.
ENV FLASK_DEBUG=false
ENV PORT=5000

# Production WSGI server
CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:${PORT:-5000} --workers 2 --timeout 120 app:app"]