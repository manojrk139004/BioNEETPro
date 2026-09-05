import os as _os
_os.environ.setdefault("DEV_AUTH_MODE", "true")  # functional suite runs in documented dev auth mode
from app import api_flashcard_create, api_flashcards_due, api_flashcard_review, api_flashcard_stats
from flask import Flask
import json

app = Flask(__name__)
app.config['TESTING'] = True

# Test the full flashcard flow
with app.test_request_context('/api/flashcards', method='POST', json={
    'front': 'What is the function of mitochondria?',
    'back': 'ATP production via cellular respiration',
    'concept_id': 'BIO-C08-01',
    'chapter_id': 'c08'
}):
    from app import api_flashcard_create
    result = api_flashcard_create()
    card_data = result.get_json()
    print("Create Flashcard:", json.dumps(card_data, indent=2))
    card_id = card_data['card_id']

with app.test_request_context('/api/flashcards/due', query_string={'student_id': 'test_student'}):
    from app import api_flashcards_due
    result = api_flashcards_due()
    print("Due Flashcards:", json.dumps(result.get_json(), indent=2))

# Review the flashcard
with app.test_request_context('/api/flashcards/review', method='POST', json={
    'card_id': card_id,
    'is_correct': True
}):
    from app import api_flashcard_review
    result = api_flashcard_review()
    print("Review Result:", json.dumps(result.get_json(), indent=2))

# Check stats after review
with app.test_request_context('/api/flashcards/stats', query_string={'student_id': 'test_student'}):
    from app import api_flashcard_stats
    result = api_flashcard_stats()
    print("Flashcard Stats:", json.dumps(result.get_json(), indent=2))

# Check due again
with app.test_request_context('/api/flashcards/due', query_string={'student_id': 'test_student'}):
    from app import api_flashcards_due
    result = api_flashcards_due()
    print("Due Flashcards After Review:", json.dumps(result.get_json(), indent=2))