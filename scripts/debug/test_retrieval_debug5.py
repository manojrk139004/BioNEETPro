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

combined = kb_results + tb_results

# Apply BM25 boost and canonical concept boost like in search()
for r in combined:
    r["hybrid_score"] = round(float(r.get("hybrid_score", 0)) + retrieval_engine._bm25_boost(
        query_tokens, str(r.get("title", "")), str(r.get("topic", ""))), 4)
    if canonical_concept and canonical_concept.lower() in str(r.get("title", "")).lower():
        r["hybrid_score"] = round(float(r["hybrid_score"]) + 0.04, 4)

# Now check the post-filter demotion logic
_vocab_kb = set(retrieval_engine.kb_vectorizer.vocabulary_.keys()) if retrieval_engine.kb_vectorizer else set()
_vocab_tb = set(retrieval_engine.tb_vectorizer.vocabulary_.keys()) if retrieval_engine.tb_vectorizer else set()
_rares_in_vocab = [t for t in _rares if t in _vocab_kb or t in _vocab_tb]
_phrases_in_vocab = [p for p in _phrases if any(w in _vocab_kb or w in _vocab_tb for w in p.split())]
_ultras_in_vocab = [u for u in _ultras if u in _vocab_kb or u in _vocab_tb]

print("rares_in_vocab:", _rares_in_vocab)
print("phrases_in_vocab:", _phrases_in_vocab)
print("ultras_in_vocab:", _ultras_in_vocab)

_hays = [(str(r.get("title", "")) + " " + str(r.get("topic", "")) + " "
          + str(r.get("definition", ""))).lower() for r in combined]

def _holds(h: str) -> bool:
    if _rares_in_vocab and any(retrieval_engine._term_holds(h, t) for t in _rares_in_vocab):
        return True
    return any(re.search(r"(?<!\w)" + re.escape(ph.lower()) + r"(?!\w)", h)
               for ph in (_phrases_in_vocab or []))

def _holds_all(h: str) -> bool:
    return bool(_rares_in_vocab) and all(retrieval_engine._term_holds(h, t) for t in _rares_in_vocab)

# Check which candidates hold the rarest term
print("Candidates holding 'cell':")
for i, (r, h) in enumerate(zip(combined, _hays)):
    holds = _holds(h)
    print("  {}: holds={} | title={} | hybrid={:.4f}".format(
        i, holds, r.get('title', '')[:50], r.get('hybrid_score', 0)))

print("\nHolders of 'cell':")
holders = [(i, r, h) for i, (r, h) in enumerate(zip(combined, _hays)) if _holds(h)]
for i, r, h in holders:
    print("  {}: {} | hybrid={:.4f}".format(i, r.get('title', '')[:50], r.get('hybrid_score', 0)))

# Now apply demotion
if any(_holds(h) for h in _hays):
    print("\nApplying demotion...")
    for r, h in zip(combined, _hays):
        if not _holds(h):
            old_score = r["hybrid_score"]
            r["hybrid_score"] = round(float(r["hybrid_score"]) - 0.15, 4)
            print("  DEMOTED: {} | {:.4f} -> {:.4f}".format(r.get('title', '')[:50], old_score, r["hybrid_score"]))
        elif _holds_all(h):
            old_score = r["hybrid_score"]
            r["hybrid_score"] = round(float(r["hybrid_score"]) + 0.10, 4)
            print("  BOOSTED: {} | {:.4f} -> {:.4f}".format(r.get('title', '')[:50], old_score, r["hybrid_score"]))

combined.sort(key=lambda r: r["hybrid_score"], reverse=True)

print("\nAfter demotion:")
for i, r in enumerate(combined[:10]):
    print("{}. {} | hybrid={:.4f}".format(i+1, r.get('title', '')[:60], r.get('hybrid_score', 0)))