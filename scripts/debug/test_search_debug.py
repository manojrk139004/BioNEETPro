from retrieval_engine import retrieval_engine

test_queries = [
    "teach me about cell",
    "teach me abt cell",
    "teach me about brain",
]

for q in test_queries:
    results = retrieval_engine.search(q, top_k=5)
    print("Query:", q)
    for i, r in enumerate(results[:3]):
        print("  {}. {} | hybrid={:.4f} | origin={}".format(
            i+1, r.get('title', '')[:60], r.get('hybrid_score', 0), r.get('origin', '')))
    print()