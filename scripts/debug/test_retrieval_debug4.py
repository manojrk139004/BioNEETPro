from retrieval_engine import retrieval_engine
from concept_normalizer import concept_normalizer
import re

query = "teach me about cell"
clean_query = re.sub(r"[^\w\s]", " ", query).lower()
rewritten = retrieval_engine.rewrite_query(query)
_vec_toks = retrieval_engine._content_vector_tokens(clean_query) + retrieval_engine._content_vector_tokens(
    re.sub(r"[^\w\s]", " ", rewritten).lower())
_morphs = set()
for _tok in _vec_toks:
    _morphs.update(retrieval_engine._morph_variants(_tok))
clean_search = f"{' '.join(_vec_toks)} {' '.join(_vec_toks)} {' '.join(sorted(_morphs))}".strip()

canonical_concept = concept_normalizer.get_canonical_concept_name(query)
if canonical_concept and canonical_concept.lower() not in clean_search:
    clean_search += f" {canonical_concept.lower()}"

query_tokens = set(clean_search.split())
raw_tokens = set(clean_query.split())
_rares = retrieval_engine._rarest_terms(clean_query)
_phrases = retrieval_engine._phrase_hits(clean_query)
_ultras = retrieval_engine._ultra_terms(clean_query)

kb_results = retrieval_engine._retrieve_kb_candidates(
    clean_query, clean_search, query_tokens, raw_tokens,
    canonical_concept, None, None,
    _rares, _phrases, _ultras,
)
tb_results = retrieval_engine._retrieve_textbook_candidates(
    clean_query, clean_search, query_tokens, raw_tokens,
    canonical_concept, None, None,
    _rares, _phrases, _ultras,
)

# Check haystacks for the top KB results
combined = kb_results + tb_results

# Apply BM25 boost and canonical concept boost like in search()
for r in combined:
    r["hybrid_score"] = round(float(r.get("hybrid_score", 0)) + retrieval_engine._bm25_boost(
        query_tokens, str(r.get("title", "")), str(r.get("topic", ""))), 4)
    if canonical_concept and canonical_concept.lower() in str(r.get("title", "")).lower():
        r["hybrid_score"] = round(float(r["hybrid_score"]) + 0.04, 4)

combined.sort(key=lambda r: r["hybrid_score"], reverse=True)

print("After BM25 boost and canonical boost:")
for i, r in enumerate(combined[:10]):
    hay = str(r.get("title", "")) + " " + str(r.get("topic", "")) + " " + str(r.get("definition", ""))
    print("{}. {} | hybrid={:.4f} | origin={}".format(
        i+1, r.get('title', '')[:60], r.get('hybrid_score', 0), r.get('origin', '')))