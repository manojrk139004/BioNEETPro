from nlp_pipeline import nlp_pipeline

for q in ['Okay', 'Give an example']:
    res = nlp_pipeline.process_query(q, history=[
        {'role': 'user', 'content': 'Explain mitochondria'},
        {'role': 'assistant', 'content': 'Mitochondria is the powerhouse...'}
    ], student_id='test')
    print(f'Query: "{q}"')
    print(f'  Resolved: "{res["resolved_query"]}"')
    print(f'  Intent: {res["intent"]}')
    print()