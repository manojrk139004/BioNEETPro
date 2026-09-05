from adaptive_tutor import adaptive_tutor
from nlp_pipeline import nlp_pipeline

test_queries = [
    "teach me about cell",
    "teach me abt cell",
    "teach me about brain",
]

for q in test_queries:
    # Get the NLP processing result
    nlp_res = nlp_pipeline.process_query(q, history=[], student_id='test_search')
    print("Query:", q)
    print("  Resolved:", nlp_res['resolved_query'])
    print("  Expanded:", nlp_res['expanded_query'][:100] if nlp_res['expanded_query'] else 'None')
    print("  Canonical:", nlp_res['canonical_concept'])
    print("  Intent:", nlp_res['intent'])
    print("  Syllabus valid:", nlp_res['syllabus_valid'])
    
    # Now test with adaptive_tutor (which uses expanded_query)
    res = adaptive_tutor.generate_tutoring_response(q, student_id='test_search2')
    print("  Adaptive title:", res.get('title', '')[:60])
    print("  Mode:", res.get('mode'))
    print()