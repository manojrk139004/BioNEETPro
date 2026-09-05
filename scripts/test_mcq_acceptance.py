import sys
sys.path.insert(0, '.')
from mcq_engine import mcq_engine
from nlp_pipeline import nlp_pipeline

print("=== TEST 1: 5 MCQs on mitochondria ===")
r1 = mcq_engine.generate_mcqs("give me 5 MCQs on mitochondria", student_id="test_mcq")
print(f"Topic: {r1['topic']} | Count: {r1['count']} | Diff: {r1['difficulty']}")
for q in r1['mcqs'][:2]:
    print(f"  Q: {q['question'][:80]}...")
    print(f"  Ans: {q['correct_answer']}")

print("\n=== TEST 2: easy MCQs on cell division ===")
r2 = mcq_engine.generate_mcqs("give me easy MCQs on cell division", student_id="test_mcq")
print(f"Topic: {r2['topic']} | Count: {r2['count']} | Diff: {r2['difficulty']}")
for q in r2['mcqs'][:2]:
    print(f"  Q: {q['question'][:80]}...")
    print(f"  Ans: {q['correct_answer']}")

print("\n=== TEST 3: Contextual 3 questions ===")
nlp_pipeline.context_tracker.track_concept("test_mcq", "BIO-C08-01", "Mitochondria and ATP Synthesis", "Mitochondria")
r3 = mcq_engine.generate_mcqs("give me 3 questions", student_id="test_mcq")
print(f"Topic: {r3['topic']} | Count: {r3['count']} | Diff: {r3['difficulty']}")
for q in r3['mcqs'][:2]:
    print(f"  Q: {q['question'][:80]}...")
    print(f"  Ans: {q['correct_answer']}")

print("\n=== TEST 4: questions from weak topics ===")
r4 = mcq_engine.generate_mcqs("give me questions from my weak topics", student_id="test_mcq")
print(f"Topic: {r4['topic']} | Count: {r4['count']} | Diff: {r4['difficulty']}")
