from adaptive_tutor import adaptive_tutor
from nlp_pipeline import nlp_pipeline

# Check what the NLP pipeline returns for "Okay" with focal context
res = nlp_pipeline.process_query('Okay', history=[
    {'role': 'user', 'content': 'Explain mitochondria'},
    {'role': 'assistant', 'content': 'Mitochondria is the powerhouse...'}
], student_id='test_fu3')

print('Resolved:', res['resolved_query'])
print('Intent:', res['intent'])
print('Syllabus valid:', res['syllabus_valid'])

# Now test the full flow
res2 = adaptive_tutor.generate_tutoring_response('Okay', student_id='test_fu3', history=[
    {'role': 'user', 'content': 'Explain mitochondria'},
    {'role': 'assistant', 'content': 'Mitochondria is the powerhouse...'}
])
print('Mode:', res2.get('mode'))
print('Follow-up type:', res2.get('follow_up_type'))