from retrieval_engine import retrieval_engine
results = retrieval_engine.search('teach me about cell', top_k=5)
for i, r in enumerate(results):
    title = r.get('title', '')
    base_cos = r.get('base_cosine', 0)
    hybrid = r.get('hybrid_score', 0)
    char_fb = r.get('char_fallback_used', False)
    print('{}. {} | word_cosine={:.4f} | hybrid={:.4f} | char_fallback={}'.format(
        i+1, title, base_cos, hybrid, char_fb))