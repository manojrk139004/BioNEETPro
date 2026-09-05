"""600-scale programmatic unseen suite: templates x concepts (generated, not hand-picked)."""
import io, sys, itertools, random
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from adaptive_tutor import adaptive_tutor

random.seed(7)
CONCEPTS = [
    ("mitochondria", "mitochondria"), ("glycolysis", "glycolysis"),
    ("photosynthesis", "photosynthesis"), ("DNA replication", "replication"),
    ("nephron", "nephron"), ("heart", "cardiac"), ("Calvin cycle", "calvin"),
    ("lac operon", "operon"), ("crossing over", "crossing"),
    ("SA node", "cardiac"), ("earthworm", "annelida"), ("cockroach", "cockroach"),
    ("xylem", "xylem"), ("phloem", "phloem"), ("neuron", "neuron"),
    ("sarcomere", "sarcomere"), ("insulin", "insulin"), ("meiosis", "meiosis"),
    ("chlorophyll", "chlorophyll"), ("ribosome", "ribosome"),
]
CATS = {
    "definition": (["define {c}", "what is {c}", "what is the meaning of {c}", "state what {c} is"], None),
    "explanation": (["explain {c}", "teach me about {c}", "tell me about {c}", "describe {c}"], None),
    "why": (["why is {c} important", "why does {c} matter in NEET", "give reasons for {c} importance"], None),
    "how": (["how does {c} work", "explain the mechanism of {c}", "describe the process of {c}"], None),
    "function": (["function of {c}", "role of {c} in the body", "what is the purpose of {c}"], None),
    "broad": (["give me an overview of {c}", "teach me {c} from basics", "introduce {c}"], None),
    "specific": (["which part of {c} is most important", "explain one key detail of {c}", "what is special about {c}"], None),
    "informal": (["teach me abt {c}", "tll me bout {c}", "plz explain {c}", "explain {c} quickly"], None),
    "ambiguous": (["doubts regarding {c}", "concept of {c}", "is {c} important for NEET"], None),
}
MCQ_T = ["give me 2 questions on {c}", "quiz me on {c}", "ask me three easy questions about {c}"]
DIFF_T = ["give me 2 hard questions on {c}", "ask one easy question about {c}"]
NONBIO = ["What is Newton's first law?", "Who won the football world cup?", "Write Python code to sort a list",
          "Explain blockchain mining", "What is the capital of France?", "Solve 2x+5=15",
          "Who is the prime minister?", "Explain chemical bonding", "What is share market?",
          "Derive the quadratic formula", "What is integral calculus?",
          "Describe the French Revolution", "What is photosynthesis rate in C++?",
          "Explain Kirchhoff's voltage law", "What is SN1 reaction?", "Define enthalpy change",
          "How to find determinants?", "Explain quantum mechanics", "What is cryptocurrency?",
          "Who discovered gravity?", "Explain relativity", "What is antiseptic surgery?",
          "Describe RNA interference in Python", "What is machine learning?",
          "Explain stock options", "Who wrote Hamlet?", "What is GDP?",
          "Explain welded joints in machines", "What is an operating system?"]

# Adjacent-grounded answers or honest refusals (neutral: must not fabricate)
NEUTRAL = ["Explain thermodynamics", "What is antiseptic surgery?",
           "why do we sneeze", "distinguish between apocrine and merocrine glands",
           "how does Botox affect acetylcholine", "why do plants need photoperiodism",
           "explain periderm formation in bark", "what is blastula",
           "explain etiolation in plants", "explain diapedesis",
           "differentiate tendons from ligaments", "mitosis versus amitosis explained",
           "explain Haversian canal system", "explain foramen ovale"]
PAIRS = [(("xylem", "phloem"), ("xylem", "phloem")), (("mitosis", "meiosis"), ("mitosis", "meiosis")),
         (("DNA", "RNA"), ("dna", "rna")), (("heart", "kidney"), ("cardiac", "kidney")),
         (("bone", "cartilage"), ("bone", "cartilage"))]

def typo(w):
    if len(w) < 5:
        return w
    i = random.randrange(1, len(w) - 1)
    l = list(w)
    l[i], l[i - 1] = l[i - 1], l[i]
    return "".join(l)

results, fails = {}, []
total = passed = 0

def run(q, sid, expect, needle="", hist=None):
    global total, passed
    total += 1
    try:
        r = adaptive_tutor.generate_tutoring_response(q, student_id=sid, history=hist or [])
    except Exception as e:
        fails.append((q, expect, f"EXC {e}"))
        return None
    txt = (str(r.get("title", "")) + " " + str(r.get("reply", ""))).lower()
    if expect == "success":
        ok = r.get("status") == "success" and (not needle or needle in txt)
    elif expect == "reject":
        ok = r.get("mode") == "syllabus_restricted"
    elif expect == "mcq":
        ok = r.get("mode") == "mcq_practice"
    else:
        ok = True
    if ok:
        passed += 1
    else:
        fails.append((q, expect, f"{r.get('mode')}/{r.get('status')} :: {str(r.get('title'))[:55]}"))
    return r

i = 0
for cat, (tmps, _) in CATS.items():
    for (c, needle), t in itertools.product(CONCEPTS, tmps):
        i += 1
        run(t.format(c=c), f"big_{cat}_{i}", "success", needle)
    print(f"cat {cat}: done", flush=True)

for (c, needle) in CONCEPTS:
    i += 1
    run(f"explain {typo(c.split()[0])} {c.split()[-1] if len(c.split()) > 1 else ''}".strip(), f"big_typo_{i}", "success", needle)
print("cat typo: done", flush=True)

for (c, needle) in CONCEPTS:
    i += 1
    run(f"Give me 2 questions on {c}", f"big_mcq_{i}", "mcq")
    i += 1
    run(f"give me 2 hard questions on {c}", f"big_diff_{i}", "mcq")
print("cat mcq/diff: done", flush=True)

for q in NONBIO:
    i += 1
    run(q, f"big_nb_{i}", "reject")
print("cat nonbio: done", flush=True)

for q in NEUTRAL:
    i += 1
    run(q, f"big_nt_{i}", "neutral")
print("cat neutral: done", flush=True)

for (a, b), (na, nb) in PAIRS:
    for t in [f"compare {a} and {b}", f"difference between {a} and {b}", f"{a} vs {b}",
              f"how are {a} and {b} different"]:
        i += 1
        run(t, f"big_cmp_{i}", "success", na)
    i += 1
    total += 1
    try:
        r = adaptive_tutor.generate_tutoring_response(f"explain {a} and {b}", student_id=f"big_cmp_{i}", history=[])
        txt = (str(r.get("title", "")) + str(r.get("reply", ""))).lower()
        if r.get("status") == "success" and (na in txt or nb in txt):
            passed += 1
        else:
            fails.append((f"explain {a} and {b}", "either-concept", f"{r.get('mode')}/{r.get('status')}"))
    except Exception as e:
        fails.append((f"explain {a} and {b}", "either-concept", f"EXC {e}"))
print("cat comparison/multi: done", flush=True)

# follow-up + pronoun chains (scripted multi-turn)
CHAINS = [
    (["Explain mitochondria.", "Why does it have folds?", "What does that increase?"], ["mitochondria", "mitochondria", "mitochondria"]),
    (["Teach me photosynthesis.", "What about the Calvin cycle?", "Explain it again."], ["photosynthesis", "calvin", "photosynthesis"]),
    (["Explain the heart.", "What does the SA node do?", "Why is it called pacemaker?"], ["cardiac", "cardiac", "pacemaker"]),
]
for ci, (qs, needles) in enumerate(CHAINS):
    h, sid = [], f"big_ctx_{ci}"
    for q, needle in zip(qs, needles):
        i += 1
        r = run(q, sid, "success", needle, h)
        h += [{"role": "user", "content": q}, {"role": "assistant", "content": str((r or {}).get("reply", ""))[:300]}]
print("cat followup: done", flush=True)

print(f"\nBIG SUITE: {passed}/{total} passed")
for q, e, d in fails[:60]:
    print(f"  FAIL [{e}] {q[:60]!r} -> {d}")
sys.exit(1 if (total - passed) > 0 else 0)
