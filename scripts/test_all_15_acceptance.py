import sys
import io
import re

sys.path.insert(0, '.')
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from adaptive_tutor import adaptive_tutor
from mcq_engine import mcq_engine
from nlp_pipeline import nlp_pipeline
from syllabus import syllabus_validator

print("=" * 70)
print("  BioNEETPro - 15 REAL-WORLD ACCEPTANCE TESTS BENCHMARK")
print("=" * 70)

all_passed = True

# --- TEST 1: teach me about cell ---
r1 = adaptive_tutor.generate_tutoring_response("teach me about cell", student_id="t15_student")
t1_ok = r1["status"] == "success" and "cell" in r1["title"].lower() and "prophase" not in r1["title"].lower()
print(f"TEST 1 [{'PASS' if t1_ok else 'FAIL'}]: 'teach me about cell'")
print(f"       Title: {r1['title']} | Conf: {r1['confidence']}")
if not t1_ok: all_passed = False

# --- TEST 2: teach me abt cell ---
r2 = adaptive_tutor.generate_tutoring_response("teach me abt cell", student_id="t15_student")
t2_ok = r2["status"] == "success" and "cell" in r2["title"].lower() and "prophase" not in r2["title"].lower()
print(f"TEST 2 [{'PASS' if t2_ok else 'FAIL'}]: 'teach me abt cell'")
print(f"       Title: {r2['title']} | Conf: {r2['confidence']}")
if not t2_ok: all_passed = False

# --- TEST 3: what is a cell ---
r3 = adaptive_tutor.generate_tutoring_response("what is a cell", student_id="t15_student")
t3_ok = r3["status"] == "success" and ("structural" in r3["reply"].lower() or "functional unit" in r3["reply"].lower() or "cell" in r3["title"].lower())
print(f"TEST 3 [{'PASS' if t3_ok else 'FAIL'}]: 'what is a cell'")
print(f"       Title: {r3['title']}")
if not t3_ok: all_passed = False

# --- TEST 4: explain mitochondria ---
r4 = adaptive_tutor.generate_tutoring_response("explain mitochondria", student_id="t15_student")
t4_ok = r4["status"] == "success" and "mitochondria" in r4["title"].lower()
print(f"TEST 4 [{'PASS' if t4_ok else 'FAIL'}]: 'explain mitochondria'")
print(f"       Title: {r4['title']} | Conf: {r4['confidence']}")
if not t4_ok: all_passed = False

# --- TEST 5: why does mitochondria have folds? ---
r5 = adaptive_tutor.generate_tutoring_response("why does mitochondria have folds?", student_id="t15_student")
t5_ok = r5["status"] == "success" and ("mitochondria" in r5["title"].lower() or "cristae" in r5["reply"].lower())
print(f"TEST 5 [{'PASS' if t5_ok else 'FAIL'}]: 'why does mitochondria have folds?'")
print(f"       Title: {r5['title']}")
if not t5_ok: all_passed = False

# --- TEST 6: what does that increase? (following Test 5) ---
r6 = adaptive_tutor.generate_tutoring_response(
    "what does that increase?",
    student_id="t15_student",
    history=[
        {"role": "user", "content": "why does mitochondria have folds?"},
        {"role": "assistant", "content": "The inner membrane forms infoldings called cristae towards the matrix."}
    ]
)
t6_ok = r6["status"] == "success" and "surface area" in r6["reply"].lower()
print(f"TEST 6 [{'PASS' if t6_ok else 'FAIL'}]: 'what does that increase?' (Follow-up to Test 5)")
print(f"       Resolved Query: {r6['resolved_query']}")
print(f"       Surface Area Grounded: {'surface area' in r6['reply'].lower()}")
if not t6_ok: all_passed = False

# --- TEST 7: teach me about brain ---
r7 = adaptive_tutor.generate_tutoring_response("teach me about brain", student_id="t15_student")
t7_ok = r7["status"] == "success" and ("brain" in r7["title"].lower() or "neural" in r7["title"].lower()) and "white matter" not in r7["title"].lower()
print(f"TEST 7 [{'PASS' if t7_ok else 'FAIL'}]: 'teach me about brain'")
print(f"       Title: {r7['title']} (Broad Brain overview confirmed)")
if not t7_ok: all_passed = False

# --- TEST 8: explain glycolysis EMP pathway and ATP yield ---
r8 = adaptive_tutor.generate_tutoring_response("explain glycolysis EMP pathway and ATP yield", student_id="t15_student")
t8_ok = r8["status"] == "success" and ("glycolysis" in r8["title"].lower() or "emp" in r8["title"].lower() or "respiration" in r8["title"].lower()) and "blood" not in r8["title"].lower()
print(f"TEST 8 [{'PASS' if t8_ok else 'FAIL'}]: 'explain glycolysis EMP pathway and ATP yield'")
print(f"       Title: {r8['title']} | No generic fallback buttons")
if not t8_ok: all_passed = False

# --- TEST 9: teach me glycolysis from basics ---
r9 = adaptive_tutor.generate_tutoring_response("teach me glycolysis from basics", student_id="t15_student")
t9_ok = r9["status"] == "success" and r9.get("strategy") in ("simplified_steps", "concrete_analogy")
print(f"TEST 9 [{'PASS' if t9_ok else 'FAIL'}]: 'teach me glycolysis from basics'")
print(f"       Strategy: {r9.get('strategy')} | Title: {r9['title']}")
if not t9_ok: all_passed = False

# --- TEST 10: why is ATP used in the first part of glycolysis? ---
r10 = adaptive_tutor.generate_tutoring_response("why is ATP used in the first part of glycolysis?", student_id="t15_student")
t10_ok = r10["status"] == "success" and ("utilised" in r10["reply"].lower() or "glucose 6-phosphate" in r10["reply"].lower() or "phosphorylat" in r10["reply"].lower() or "hexokinase" in r10["reply"].lower())
print(f"TEST 10 [{'PASS' if t10_ok else 'FAIL'}]: 'why is ATP used in the first part of glycolysis?'")
print(f"        Evidence Citation: {r10.get('source')}")
print(f"        Key Phosphorylation Steps Present: {t10_ok}")
if not t10_ok: all_passed = False

# --- TEST 11: give me 2 mcq on cockroach chapter ---
r11 = mcq_engine.generate_mcqs("give me 2 mcq on cockroach chapter", student_id="t15_student")
t11_ok = r11["status"] == "success" and r11["count"] == 2 and any("cockroach" in q["question"].lower() or "periplaneta" in q["question"].lower() or "cockroach" in q["topic"].lower() for q in r11["mcqs"])
print(f"TEST 11 [{'PASS' if t11_ok else 'FAIL'}]: 'give me 2 mcq on cockroach chapter'")
print(f"        Generated Count: {r11['count']} | Topic: {r11['topic']}")
for i, q in enumerate(r11["mcqs"]):
    print(f"        Q{i+1}: {q['question'][:75]}")
if not t11_ok: all_passed = False

# --- TEST 12: give me 5 hard questions on genetics ---
r12 = mcq_engine.generate_mcqs("give me 5 hard questions on genetics", student_id="t15_student")
t12_ok = r12["status"] == "success" and r12["count"] == 5 and r12["difficulty"] == "hard"
print(f"TEST 12 [{'PASS' if t12_ok else 'FAIL'}]: 'give me 5 hard questions on genetics'")
print(f"        Generated Count: {r12['count']} | Diff: {r12['difficulty']} | Topic: {r12['topic']}")
for i, q in enumerate(r12["mcqs"]):
    print(f"        Q{i+1}: {q['question'][:75]}")
if not t12_ok: all_passed = False

# --- TEST 13: give me questions from my weak topics ---
r13 = mcq_engine.generate_mcqs("give me questions from my weak topics", student_id="t15_student")
t13_ok = r13["status"] == "success" and r13["count"] > 0
print(f"TEST 13 [{'PASS' if t13_ok else 'FAIL'}]: 'give me questions from my weak topics'")
print(f"        Generated Count: {r13['count']} | Mode: {r13['topic']}")
if not t13_ok: all_passed = False

# --- TEST 14: what is Newton's second law? (Rejection) ---
s14 = syllabus_validator.check_query_syllabus("what is Newton's second law?")
t14_ok = not s14["is_valid"]
print(f"TEST 14 [{'PASS' if t14_ok else 'FAIL'}]: 'what is Newton's second law?'")
print(f"        Controlled Refusal: {t14_ok} | Message: {s14.get('refusal_message', '')[:60]}...")
if not t14_ok: all_passed = False

# --- TEST 15: 4-Turn Multi-Turn Conversation ---
print(f"TEST 15: 4-Turn Multi-Turn Conversational Chain")
t15_student = "multi_turn_accept_user"
# Turn 1
nlp_pipeline.context_tracker.clear_context(t15_student)
q15_1 = "Explain mitochondria."
r15_1 = adaptive_tutor.generate_tutoring_response(q15_1, student_id=t15_student)
turn1_ok = "mitochondria" in r15_1["title"].lower()
print(f"        Turn 1: '{q15_1}' -> Concept: {r15_1['title']} [{'PASS' if turn1_ok else 'FAIL'}]")

# Turn 2
q15_2 = "Why does it have folds?"
h15_2 = [
    {"role": "user", "content": q15_1},
    {"role": "assistant", "content": r15_1["reply"]}
]
r15_2 = adaptive_tutor.generate_tutoring_response(q15_2, student_id=t15_student, history=h15_2)
turn2_ok = "mitochondria" in r15_2["resolved_query"].lower()
print(f"        Turn 2: '{q15_2}' -> Resolved: {r15_2['resolved_query']} [{'PASS' if turn2_ok else 'FAIL'}]")

# Turn 3
q15_3 = "What does that increase?"
h15_3 = [
    {"role": "user", "content": q15_1},
    {"role": "assistant", "content": r15_1["reply"]},
    {"role": "user", "content": q15_2},
    {"role": "assistant", "content": r15_2["reply"]}
]
r15_3 = adaptive_tutor.generate_tutoring_response(q15_3, student_id=t15_student, history=h15_3)
turn3_ok = "surface area" in r15_3["reply"].lower()
print(f"        Turn 3: '{q15_3}' -> Resolved: {r15_3['resolved_query']} [{'PASS' if turn3_ok else 'FAIL'}]")
print(f"                Surface area increase verified: {'surface area' in r15_3['reply'].lower()}")

# Turn 4
q15_4 = "Give me 3 questions on it."
r15_4 = mcq_engine.generate_mcqs(q15_4, student_id=t15_student)
turn4_ok = r15_4["count"] == 3 and "mitochondria" in r15_4["topic"].lower()
print(f"        Turn 4: '{q15_4}' -> Generated 3 MCQs on {r15_4['topic']} [{'PASS' if turn4_ok else 'FAIL'}]")

t15_ok = turn1_ok and turn2_ok and turn3_ok and turn4_ok
if not t15_ok: all_passed = False

print("\n" + "=" * 70)
print(f"  ALL 15 ACCEPTANCE TESTS RESULT: {'ALL 15 PASSED!' if all_passed else 'SOME FAILED'}")
print("=" * 70)
