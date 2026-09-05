FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy dependencies
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Backend source modules
COPY app.py ./
COPY adaptive_tutor.py ./
COPY concept_graph.py ./
COPY concept_normalizer.py ./
COPY content_classifier.py ./
COPY dialogue_state.py ./
COPY fallback_controller.py ./
COPY figure_extractor.py ./
COPY firestore_store.py ./
COPY flashcard_backend.py ./
COPY knowledge_ingestion.py ./
COPY learner_model.py ./
COPY mcq_bank_generator.py ./
COPY mcq_engine.py ./
COPY ncert_ingestion.py ./
COPY nlp_pipeline.py ./
COPY policy_engine.py ./
COPY response_validator.py ./
COPY retrieval_engine.py ./
COPY score_predictor.py ./
COPY syllabus.py ./
COPY tutor_engine.py ./
COPY update_kb.py ./

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