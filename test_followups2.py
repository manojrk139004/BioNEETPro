from adaptive_tutor import adaptive_tutor

# First set up a real student with focal concept
adaptive_tutor.generate_tutoring_response('Explain mitochondria', student_id='test_fu3')
print('Focal concept set')

test_cases = [
    ('What does it do?', 'what_does_it_do'),
    ('Make it harder', 'make_it_harder'),
    ('Make it easier', 'make_it_easier'),
    ('Okay', 'okay'),
    ('Give an example', 'example'),
]

for query, expected_type in test_cases:
    res = adaptive_tutor.generate_tutoring_response(query, student_id='test_fu3', history=[
        {'role': 'user', 'content': 'Explain mitochondria'},
        {'role': 'assistant', 'content': 'Mitochondria is the powerhouse...'}
    ])
    actual_type = res.get('follow_up_type')
    status = 'PASS' if actual_type == expected_type else 'FAIL'
    print(f'{status}: "{query}" -> {actual_type} (expected {expected_type})')