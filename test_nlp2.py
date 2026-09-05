from nlp_pipeline import nlp_pipeline

# Test with context
res = nlp_pipeline.process_query('Give an example', history=[
    {'role': 'user', 'content': 'Explain mitochondria'},
    {'role': 'assistant', 'content': 'Mitochondria is the powerhouse of the cell...'}
], student_id='test')

print('Resolved:', res['resolved_query'])
print('Intent:', res['intent'])
print('Syllabus valid:', res['syllabus_valid'])
print('Focal concept:', res.get('focal_concept'))