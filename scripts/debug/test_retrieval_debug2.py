from retrieval_engine import retrieval_engine
import re

# Check what the rarest terms are for this query
query = "teach me about cell"
clean_query = re.sub(r"[^\w\s]", " ", query).lower()
print('clean_query:', clean_query)

# Check what _rarest_terms returns
rares = retrieval_engine._rarest_terms(clean_query)
print('rarest terms:', rares)

# Check what _phrase_hits returns
phrases = retrieval_engine._phrase_hits(clean_query)
print('phrases:', phrases)

# Check what _ultra_terms returns
ultras = retrieval_engine._ultra_terms(clean_query)
print('ultras:', ultras)

# Check the vocabulary
vocab_kb = set(retrieval_engine.kb_vectorizer.vocabulary_.keys()) if retrieval_engine.kb_vectorizer else set()
vocab_tb = set(retrieval_engine.tb_vectorizer.vocabulary_.keys()) if retrieval_engine.tb_vectorizer else set()

rares_in_vocab = [t for t in retrieval_engine._rarest_terms(clean_query) if t in vocab_kb or t in vocab_tb]
print('rares_in_vocab:', rares_in_vocab)