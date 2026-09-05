from mcq_engine import mcq_engine
tests = [
    ('give me five questions on heart', 5),
    ('quiz me with three on respiration', 3),
    ('give me two MCQs', 2),
    ('ask 10 questions', 10),
    ('give me seven questions', 7),
    ('generate twenty mcqs', 20),
]
for q, expected in tests:
    parsed = mcq_engine.parse_mcq_request(q, student_id='test')
    actual = parsed['requested_count']
    status = 'OK' if actual == expected else 'FAIL'
    print(f'{status}: "{q}" -> {actual} (expected {expected})')