import json

# Load the textbook index
with open('data/ncert_textbook_index.json', 'r', encoding='utf-8') as f:
    chunks = json.load(f)

# Search for cohesion-tension and munch/pressure flow terms
cohesion_terms = set()
munch_terms = set()

for c in chunks:
    text = (c.get('text', '') + ' ' + c.get('section', '') + ' ' + ' '.join(c.get('keywords', []))).lower()
    if 'cohesion' in text or 'tension' in text:
        for w in text.split():
            if 'cohesion' in w or 'tension' in w:
                cohesion_terms.add(w)
    if 'munch' in text or 'pressure flow' in text:
        for w in text.split():
            if 'munch' in w or 'pressure' in w or 'flow' in w:
                munch_terms.add(w)

print("Cohesion/tension terms:", sorted(cohesion_terms))
print("Munch/pressure flow terms:", sorted(munch_terms))

# Also check which chapters these appear in
for c in chunks:
    text = (c.get('text', '') + ' ' + c.get('section', '')).lower()
    if 'cohesion-tension' in text or 'cohesion tension' in text:
        print(f"Cohesion-tension in: {c.get('chapter_title')} - {c.get('section')}")
    if 'munch' in text or 'pressure flow' in text:
        print(f"Munch/pressure flow in: {c.get('chapter_title')} - {c.get('section')}")