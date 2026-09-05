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
for r in kb_results[:5]:
    hay = str(r.get("title", "")) + " " + str(r.get("topic", "")) + " " + str(r.get("definition", ""))
    print("KB: {} | hybrid={:.4f} | has_cell={}".format(
        r.get('title', '')[:50], r.get('hybrid_score', 0), 'cell' in hay.lower()))

for r in tb_results[:5]:
    hay = str(r.get("title", "")) + " " + str(r.get("topic", "")) + " " + str(r.get("definition", ""))
    print("TB: {} | hybrid={:.4f} | has_cell={}".format(
        r.get('title', '')[:50], r.get('hybrid_score', 0), 'cell' in hay.lower()))