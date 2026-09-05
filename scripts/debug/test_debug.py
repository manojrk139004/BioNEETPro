from nlp_pipeline import nlp_pipeline

# Check what the NLP pipeline returns for "Okay" with focal context
res = nlp_pipeline.process_query('Okay', history=[
    {'role': 'user', 'content': 'Explain mitochondria'},
    {'role': 'assistant', 'content': 'Mitochondria is the powerhouse...'}
], student_id='test_fu3')

print('Resolved:', res['resolved_query'])
print('Intent:', res['intent'])
print('Syllabus valid:', res['syllabus_valid'])
print('Syllabus data:', res['syllabus_data'])
print('Focal concept:', res.get('focal_concept'))

# Check focal from context tracker directly
focal = nlp_pipeline.context_tracker.get_focal_concept('test_fu3')
print('Direct focal:', focal)