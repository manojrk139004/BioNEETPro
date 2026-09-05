import json

with open('data/ncert_textbook_index.json', 'r', encoding='utf-8') as f:
    chunks = json.load(f)

# Search for cohesion-tension and munch/pressure flow terms
for c in chunks:
    text = (c.get('text', '') + ' ' + c.get('section', '') + ' ' + ' '.join(c.get('keywords', []))).lower()
    if 'cohesion' in text and 'tension' in text:
        print(f"Cohesion-tension in: {c.get('chapter_title')} - {c.get('section')}")
        print(f"  Keywords: {c.get('keywords')}")
        print()
    if 'munch' in text or 'pressure flow' in text:
        print(f"Munch/pressure flow in: {c.get('chapter_title')} - {c.get('section')}")
        print(f"  Keywords: {c.get('keywords')}")
        print()

# Also search for "transpiration pull" and "mass flow"
for c in chunks:
    text = (c.get('text', '') + ' ' + c.get('section', '')).lower()
    if 'transpiration pull' in text:
        print(f"Transpiration pull in: {c.get('chapter_title')} - {c.get('section')}")
        print(f"  Keywords: {c.get('keywords')}")
        print()
    if 'mass flow' in text:
        print(f"Mass flow in: {c.get('chapter_title')} - {c.get('section')}")
        print(f"  Keywords: {c.get('keywords')}")
        print()