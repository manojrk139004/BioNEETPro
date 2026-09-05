from adaptive_tutor import adaptive_tutor
from nlp_pipeline import nlp_pipeline

# First, have a real interaction that sets focal concept
res1 = adaptive_tutor.generate_tutoring_response('Explain mitochondria', student_id='test_real')
print('First response mode:', res1.get('mode'))
print('Focal set:', res1.get('concept_id'))

# Now check the context tracker
from nlp_pipeline import nlp_pipeline as nlp
focal = nlp.context_tracker.get_focal_concept('test_real')
print('Focal concept after first query:', focal)

# Now test follow-up
res2 = nlp.process_query('Give an example', history=[
    {'role': 'user', 'content': 'Explain mitochondria'},
    {'role': 'assistant', 'content': 'Mitochondria is the powerhouse...'}
], student_id='test_real')

print('Resolved:', res2['resolved_query'])
print('Intent:', res2['intent'])
print('Syllabus valid:', res2['syllabus_valid'])
print('Focal concept:', res2.get('focal_concept'))