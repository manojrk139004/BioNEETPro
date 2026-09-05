import sys
sys.path.insert(0, '.')
from adaptive_tutor import adaptive_tutor

student_id = "demo_student_turn_test"
history = []

print("=== TURN 1 ===")
q1 = "Explain mitochondria."
r1 = adaptive_tutor.generate_tutoring_response(q1, student_id=student_id, history=history)
print(f"User: {q1}")
print(f"Resolved: {r1['resolved_query']}")
print(f"Concept: {r1['title']}")
print(f"Confidence: {r1['confidence']}")
print(f"Source: {r1.get('source')}")
print(f"Reply Preview: {r1['reply'][:200].encode('ascii', errors='replace').decode()}...")
history.append({"role": "user", "content": q1})
history.append({"role": "assistant", "content": r1["reply"]})

print("\n=== TURN 2 ===")
q2 = "Why does it have folds?"
r2 = adaptive_tutor.generate_tutoring_response(q2, student_id=student_id, history=history)
print(f"User: {q2}")
print(f"Resolved: {r2['resolved_query']}")
print(f"Concept: {r2['title']}")
print(f"Confidence: {r2['confidence']}")
print(f"Reply Preview: {r2['reply'][:200].encode('ascii', errors='replace').decode()}...")
history.append({"role": "user", "content": q2})
history.append({"role": "assistant", "content": r2["reply"]})

print("\n=== TURN 3 ===")
q3 = "What does that increase?"
r3 = adaptive_tutor.generate_tutoring_response(q3, student_id=student_id, history=history)
print(f"User: {q3}")
print(f"Resolved: {r3['resolved_query']}")
print(f"Concept: {r3['title']}")
print(f"Confidence: {r3['confidence']}")
print(f"Reply Preview: {r3['reply'][:200].encode('ascii', errors='replace').decode()}...")
history.append({"role": "user", "content": q3})
history.append({"role": "assistant", "content": r3["reply"]})
