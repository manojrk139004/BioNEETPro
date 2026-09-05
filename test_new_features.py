import os as _os
_os.environ.setdefault("DEV_AUTH_MODE", "true")  # functional suite runs in documented dev auth mode
from app import api_score_predict, api_flashcard_create, api_flashcards_due, api_flashcard_review, api_flashcard_stats
from flask import Flask
import json

# Create a test app context
app = Flask(__name__)
app.config['TESTING'] = True

with app.test_request_context('/api/score/predict', query_string={'student_id': 'test_student'}):
    from app import api_score_predict
    result = api_score_predict()
    print("Score Predict:", result.get_json())

with app.test_request_context('/api/flashcards', method='POST', json={
    'front': 'What is the powerhouse of the cell?',
    'back': 'Mitochondria',
    'concept_id': 'BIO-C08-01',
    'chapter_id': 'c08'
}):
    from app import api_flashcard_create
    result = api_flashcard_create()
    print("Create Flashcard:", result.get_json())

with app.test_request_context('/api/flashcards/due', query_string={'student_id': 'test_student'}):
    from app import api_flashcards_due
    result = api_flashcards_due()
    print("Due Flashcards:", result.get_json())

with app.test_request_context('/api/flashcards/stats', query_string={'student_id': 'test_student'}):
    from app import api_flashcard_stats
    result = api_flashcard_stats()
    print("Flashcard Stats:", result.get_json())