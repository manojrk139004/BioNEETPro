from nlp_pipeline import nlp_pipeline
import json

# Check what the NLP pipeline returns for "Okay" with focal context
res = nlp_pipeline.process_query('Okay', history=[
    {'role': 'user', 'content': 'Explain mitochondria'},
    {'role': 'assistant', 'content': 'Mitochondria is the powerhouse...'}
], student_id='test_fu3')

print('Resolved:', res['resolved_query'])
print('Intent:', res['intent'])
print('Syllabus valid:', res['syllabus_valid'])

# Check focal from context tracker directly
focal = nlp_pipeline.context_tracker.get_focal_concept('test_fu3')
print('Direct focal:', focal)

# Check the syllabus check directly
from syllabus import syllabus_validator
syl = syllabus_validator.check_query_syllabus('Okay')
print('Direct syllabus check:', syl)

# Check focal concept syllabus
if focal:
    focal_syl = syllabus_validator.check_query_syllabus(focal[1])
    print('Focal syllabus:', focal_syl)