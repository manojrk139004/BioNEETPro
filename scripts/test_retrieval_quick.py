from retrieval_engine import retrieval_engine

test_queries = [
    'teach me about cell',
    'teach me abt cell',
    'what is a cell',
    'explain mitochondria',
    'why does mitochondria have folds',
    'teach me about brain',
    'how does photosynthesis work'
]

for q in test_queries:
    res = retrieval_engine.search(q, top_k=1)
    if res:
        top = res[0]
        print(f"QUERY: '{q}'")
        print(f"  Title: {top['title']}")
        print(f"  Chapter: {top['chapter_name']}")
        print(f"  Confidence: {top['confidence']} | Score: {top['hybrid_score']}")
        print(f"  Source: {top['source']}")
        print()
    else:
        print(f"QUERY: '{q}' -> NO MATCH\n")
