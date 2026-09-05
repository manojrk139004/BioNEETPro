from adaptive_tutor import adaptive_tutor

# First set up a real student with focal concept
res1 = adaptive_tutor.generate_tutoring_response('Explain mitochondria', student_id='test_fu5')
print('First response mode:', res1.get('mode'))

from nlp_pipeline import nlp_pipeline
focal = nlp_pipeline.context_tracker.get_focal_concept('test_fu5')
print('Focal concept after first query:', focal)

test_cases = [
    ('Okay', 'okay'),
    ('Give an example', 'example'),
    ('What does it do?', 'what_does_it_do'),
    ('Make it harder', 'make_it_harder'),
]

for query, expected_type in test_cases:
    res = adaptive_tutor.generate_tutoring_response(query, student_id='test_fu5', history=[
        {'role': 'user', 'content': 'Explain mitochondria'},
        {'role': 'assistant', 'content': 'Mitochondria is the powerhouse...'}
    ])
    actual_type = res.get('follow_up_type')
    mode = res.get('mode')
    status = 'PASS' if actual_type == expected_type else 'FAIL'
    print(f'{status}: "{query}" -> mode={mode}, follow_up={actual_type} (expected {expected_type})')