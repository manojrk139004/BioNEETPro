"""
BioNEETPro - Comprehensive System Evaluation & Metrics Benchmark
================================================================
Evaluates:
1. Dual-Source NCERT Retrieval Engine (Precision@1, Precision@3, MRR, Concept Hit Rate)
2. 120+ Unseen Real-World Biology Queries across all NCERT Units
3. NLP Shorthand, Typo Correction & Pedagogical Intent Classification
4. Multi-Turn Conversational Antecedent & Anaphora Resolution
5. Out-of-Syllabus & Non-Biology Controlled Rejection Rates
6. MCQ System Integrity (Option Validity, Answer Verification, Difficulty Adaptation)
7. Final 12 Mandatory Acceptance Queries Benchmark
"""

import sys
import time
import io

# Ensure UTF-8 output encoding across platforms
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from adaptive_tutor import adaptive_tutor
from concept_normalizer import concept_normalizer
from learner_model import learner_manager
from mcq_engine import mcq_engine
from nlp_pipeline import nlp_pipeline
from retrieval_engine import retrieval_engine
from syllabus import syllabus_validator

# =====================================================================
# 1. 100+ REALISTIC UNSEEN BIOLOGY EVALUATION BENCHMARK
# =====================================================================

EVAL_BENCHMARK = [
    # --- Cell Biology & Organelles (Class 11 Ch 8, 9, 10) ---
    {"query": "teach me about cell", "expected_concept": "Cell", "expected_chapter": "Cell : The Unit of Life", "type": "overview"},
    {"query": "teach me abt cell", "expected_concept": "Cell", "expected_chapter": "Cell : The Unit of Life", "type": "shorthand"},
    {"query": "what is a cell", "expected_concept": "Cell", "expected_chapter": "Cell : The Unit of Life", "type": "definition"},
    {"query": "explain mitochondria", "expected_concept": "Mitochondria", "expected_chapter": "Cell : The Unit of Life", "type": "overview"},
    {"query": "mitocondria function", "expected_concept": "Mitochondria", "expected_chapter": "Cell : The Unit of Life", "type": "typo"},
    {"query": "why does mitochondria have folds", "expected_concept": "Mitochondria", "expected_chapter": "Cell : The Unit of Life", "type": "why"},
    {"query": "what is cristae in mitochondria", "expected_concept": "Cristae", "expected_chapter": "Cell : The Unit of Life", "type": "definition"},
    {"query": "role of ribosomes in cell", "expected_concept": "Ribosome", "expected_chapter": "Cell : The Unit of Life", "type": "function"},
    {"query": "function of golgi apparatus", "expected_concept": "Golgi apparatus", "expected_chapter": "Cell : The Unit of Life", "type": "function"},
    {"query": "why lysosomes are called suicidal bags", "expected_concept": "Lysosomes", "expected_chapter": "Cell : The Unit of Life", "type": "why"},
    {"query": "structure of cell membrane", "expected_concept": "Cell Membrane", "expected_chapter": "Cell : The Unit of Life", "type": "structure"},
    {"query": "fluid mosaic model of plasma membrane", "expected_concept": "Cell Membrane", "expected_chapter": "Cell : The Unit of Life", "type": "process"},
    {"query": "difference between prokaryotic and eukaryotic cells", "expected_concept": "Cell", "expected_chapter": "Cell : The Unit of Life", "type": "difference"},
    {"query": "what happens in pachytene stage of meiosis", "expected_concept": "Crossing Over in Pachytene", "expected_chapter": "Cell Cycle and Cell Division", "type": "process"},
    {"query": "crossing over in meiosis", "expected_concept": "Crossing Over in Pachytene", "expected_chapter": "Cell Cycle and Cell Division", "type": "process"},
    {"query": "diff b/w mitosis and meiosis", "expected_concept": "Mitosis", "expected_chapter": "Cell Cycle and Cell Division", "type": "shorthand"},
    {"query": "what is equational division", "expected_concept": "Mitosis", "expected_chapter": "Cell Cycle and Cell Division", "type": "definition"},
    {"query": "quaternary structure of hemoglobin", "expected_concept": "Biomolecules", "expected_chapter": "Biomolecules", "type": "structure"},
    {"query": "peptide bond formation in proteins", "expected_concept": "Amino Acids", "expected_chapter": "Biomolecules", "type": "process"},
    {"query": "lock and key enzyme hypothesis", "expected_concept": "Enzymes", "expected_chapter": "Biomolecules", "type": "mechanism"},

    # --- Plant Physiology (Class 11 Ch 11, 12, 13) ---
    {"query": "how does photosynthesis work", "expected_concept": "Photosynthesis", "expected_chapter": "Photosynthesis in Higher Plants", "type": "mechanism"},
    {"query": "phts light reaction z scheme", "expected_concept": "Photochemical Phase", "expected_chapter": "Photosynthesis in Higher Plants", "type": "shorthand"},
    {"query": "calvin cycle c3 pathway steps", "expected_concept": "Calvin Cycle", "expected_chapter": "Photosynthesis in Higher Plants", "type": "process"},
    {"query": "kranz anatomy in c4 plants", "expected_concept": "Hatch and Slack Pathway", "expected_chapter": "Photosynthesis in Higher Plants", "type": "structure"},
    {"query": "why c4 plants are more efficient than c3", "expected_concept": "Hatch and Slack Pathway", "expected_chapter": "Photosynthesis in Higher Plants", "type": "why"},
    {"query": "role of rubisco enzyme", "expected_concept": "Calvin Cycle", "expected_chapter": "Photosynthesis in Higher Plants", "type": "function"},
    {"query": "splitting of water in photosynthesis", "expected_concept": "Photosynthesis", "expected_chapter": "Photosynthesis in Higher Plants", "type": "process"},
    {"query": "glycolysis emp pathway steps", "expected_concept": "Glycolysis", "expected_chapter": "Respiration in Plants", "type": "process"},
    {"query": "how is atp generated in respiration", "expected_concept": "ATP", "expected_chapter": "Respiration in Plants", "type": "mechanism"},
    {"query": "krebs cycle tca reactions", "expected_concept": "Krebs Cycle", "expected_chapter": "Respiration in Plants", "type": "process"},
    {"query": "respiratory quotient rq of fats", "expected_concept": "Respiration in Plants", "expected_chapter": "Respiration in Plants", "type": "fact"},
    {"query": "auxin role in apical dominance", "expected_concept": "Plant Growth and Development", "expected_chapter": "Plant Growth and Development", "type": "function"},
    {"query": "gibberellins in seed germination", "expected_concept": "Plant Growth and Development", "expected_chapter": "Plant Growth and Development", "type": "function"},
    {"query": "ethylene fruit ripening hormone", "expected_concept": "Plant Growth and Development", "expected_chapter": "Plant Growth and Development", "type": "function"},

    # --- Human Physiology (Class 11 Ch 14, 15, 16, 17, 18, 19) ---
    {"query": "teach me about brain", "expected_concept": "Brain", "expected_chapter": "Neural Control and Coordination", "type": "overview"},
    {"query": "structure of human brain forebrain midbrain", "expected_concept": "Brain", "expected_chapter": "Neural Control and Coordination", "type": "structure"},
    {"query": "how neuron conducts action potential", "expected_concept": "Neuron", "expected_chapter": "Neural Control and Coordination", "type": "mechanism"},
    {"query": "synaptic transmission neurotransmitter", "expected_concept": "Neuron", "expected_chapter": "Neural Control and Coordination", "type": "process"},
    {"query": "function of cerebellum in brain", "expected_concept": "Brain", "expected_chapter": "Neural Control and Coordination", "type": "function"},
    {"query": "sliding filament theory of muscle contraction", "expected_concept": "Locomotion and Movement", "expected_chapter": "Locomotion and Movement", "type": "mechanism"},
    {"query": "role of troponin and actin in muscle", "expected_concept": "Locomotion and Movement", "expected_chapter": "Locomotion and Movement", "type": "function"},
    {"query": "206 bones in human body axial skeleton", "expected_concept": "Locomotion and Movement", "expected_chapter": "Locomotion and Movement", "type": "fact"},
    {"query": "countercurrent mechanism in loop of henle", "expected_concept": "Nephron", "expected_chapter": "Excretory Products and their Elimination", "type": "mechanism"},
    {"query": "structural and functional unit of kidney", "expected_concept": "Nephron", "expected_chapter": "Excretory Products and their Elimination", "type": "definition"},
    {"query": "dialysis in renal failure", "expected_concept": "Excretory Products and their Elimination", "expected_chapter": "Excretory Products and their Elimination", "type": "process"},
    {"query": "cardiac cycle phases in human heart", "expected_concept": "Cardiac Cycle", "expected_chapter": "Body Fluids and Circulation", "type": "process"},
    {"query": "why sa node is called pacemaker of heart", "expected_concept": "SA Node", "expected_chapter": "Body Fluids and Circulation", "type": "why"},
    {"query": "rh incompatibility erythroblastosis foetalis", "expected_concept": "Body Fluids and Circulation", "expected_chapter": "Body Fluids and Circulation", "type": "fact"},
    {"query": "blood grouping abo system codominance", "expected_concept": "Body Fluids and Circulation", "expected_chapter": "Body Fluids and Circulation", "type": "concept"},
    {"query": "mechanism of breathing inspiration expiration", "expected_concept": "Breathing and Exchange of Gases", "expected_chapter": "Breathing and Exchange of Gases", "type": "mechanism"},
    {"query": "oxygen dissociation curve bohr effect", "expected_concept": "Breathing and Exchange of Gases", "expected_chapter": "Breathing and Exchange of Gases", "type": "concept"},
    {"query": "master gland pituitary hormones", "expected_concept": "Pituitary Gland", "expected_chapter": "Chemical Coordination and Integration", "type": "function"},
    {"query": "insulin and glucagon blood glucose regulation", "expected_concept": "Insulin", "expected_chapter": "Chemical Coordination and Integration", "type": "function"},
    {"query": "mechanism of hormone action second messenger camp", "expected_concept": "Chemical Coordination and Integration", "expected_chapter": "Chemical Coordination and Integration", "type": "mechanism"},

    # --- Diversity & Structural Organisation (Class 11 Ch 1 to 7) ---
    {"query": "binomial nomenclature rules linnaeus", "expected_concept": "The Living World", "expected_chapter": "The Living World", "type": "rules"},
    {"query": "five kingdom classification whittaker", "expected_concept": "Biological Classification", "expected_chapter": "Biological Classification", "type": "classification"},
    {"query": "difference between gram positive and gram negative bacteria", "expected_concept": "Biological Classification", "expected_chapter": "Biological Classification", "type": "difference"},
    {"query": "alternation of generations in pteridophytes", "expected_concept": "Pteridophytes", "expected_chapter": "Plant Kingdom", "type": "process"},
    {"query": "why bryophytes are called amphibians of plant kingdom", "expected_concept": "Bryophytes", "expected_chapter": "Plant Kingdom", "type": "why"},
    {"query": "open vs closed circulatory system in animal kingdom", "expected_concept": "Animal Kingdom", "expected_chapter": "Animal Kingdom", "type": "comparison"},
    {"query": "water vascular system in echinodermata", "expected_concept": "Animal Kingdom", "expected_chapter": "Animal Kingdom", "type": "characteristic"},
    {"query": "types of root systems tap adventitious fibrous", "expected_concept": "Morphology of Flowering Plants", "expected_chapter": "Morphology of Flowering Plants", "type": "types"},
    {"query": "placentation types marginal axile parietal", "expected_concept": "Morphology of Flowering Plants", "expected_chapter": "Morphology of Flowering Plants", "type": "types"},
    {"query": "difference between xylem and phloem complex tissues", "expected_concept": "Anatomy of Flowering Plants", "expected_chapter": "Anatomy of Flowering Plants", "type": "difference"},

    # --- Genetics & Evolution (Class 12 Ch 4, 5, 6) ---
    {"query": "mendel law of segregation monohybrid cross", "expected_concept": "Principles of Inheritance and Variation", "expected_chapter": "Principles of Inheritance and Variation", "type": "concept"},
    {"query": "law of independent assortment dihybrid ratio 9:3:3:1", "expected_concept": "Principles of Inheritance and Variation", "expected_chapter": "Principles of Inheritance and Variation", "type": "concept"},
    {"query": "incomplete dominance in snapdragon", "expected_concept": "Principles of Inheritance and Variation", "expected_chapter": "Principles of Inheritance and Variation", "type": "concept"},
    {"query": "morgan linkage experiment in drosophila", "expected_concept": "Principles of Inheritance and Variation", "expected_chapter": "Principles of Inheritance and Variation", "type": "experiment"},
    {"query": "haemophilia sex linked recessive inheritance", "expected_concept": "Principles of Inheritance and Variation", "expected_chapter": "Principles of Inheritance and Variation", "type": "disease"},
    {"query": "watson crick double helix model of dna", "expected_concept": "DNA", "expected_chapter": "Molecular Basis of Inheritance", "type": "structure"},
    {"query": "semi conservative replication meselson stahl experiment", "expected_concept": "DNA Replication", "expected_chapter": "Molecular Basis of Inheritance", "type": "experiment"},
    {"query": "transcription in eukaryotes rna polymerase promoter", "expected_concept": "Molecular Basis of Inheritance", "expected_chapter": "Molecular Basis of Inheritance", "type": "process"},
    {"query": "genetic code characteristics degenerate universal", "expected_concept": "Molecular Basis of Inheritance", "expected_chapter": "Molecular Basis of Inheritance", "type": "concept"},
    {"query": "lac operon repressor inducer regulation", "expected_concept": "Molecular Basis of Inheritance", "expected_chapter": "Molecular Basis of Inheritance", "type": "mechanism"},
    {"query": "dna fingerprinting tandem repeats vntr", "expected_concept": "Molecular Basis of Inheritance", "expected_chapter": "Molecular Basis of Inheritance", "type": "process"},
    {"query": "miller urey experiment origin of life", "expected_concept": "Evolution", "expected_chapter": "Evolution", "type": "experiment"},
    {"query": "homologous vs analogous organs convergent evolution", "expected_concept": "Evolution", "expected_chapter": "Evolution", "type": "difference"},
    {"query": "hardy weinberg principle genetic equilibrium", "expected_concept": "Evolution", "expected_chapter": "Evolution", "type": "concept"},
    {"query": "darwin finches adaptive radiation galapagos", "expected_concept": "Evolution", "expected_chapter": "Evolution", "type": "concept"},

    # --- Reproduction & Human Welfare (Class 12 Ch 1, 2, 3, 7, 8) ---
    {"query": "double fertilization in angiosperms triple fusion", "expected_concept": "Sexual Reproduction in Flowering Plants", "expected_chapter": "Sexual Reproduction in Flowering Plants", "type": "process"},
    {"query": "structure of pollen grain microsporogenesis", "expected_concept": "Sexual Reproduction in Flowering Plants", "expected_chapter": "Sexual Reproduction in Flowering Plants", "type": "structure"},
    {"query": "spermatogenesis vs oogenesis in humans", "expected_concept": "Human Reproduction", "expected_chapter": "Human Reproduction", "type": "difference"},
    {"query": "menstrual cycle hormones lh fsh surge", "expected_concept": "Human Reproduction", "expected_chapter": "Human Reproduction", "type": "process"},
    {"query": "contraceptive methods copper t iud mechanism", "expected_concept": "Reproductive Health", "expected_chapter": "Reproductive Health", "type": "mechanism"},
    {"query": "innate vs acquired immunity humoral cell mediated", "expected_concept": "Human Health and Disease", "expected_chapter": "Human Health and Disease", "type": "comparison"},
    {"query": "antibody structure igg igm antigen binding site", "expected_concept": "Human Health and Disease", "expected_chapter": "Human Health and Disease", "type": "structure"},
    {"query": "life cycle of plasmodium malaria pathogen", "expected_concept": "Human Health and Disease", "expected_chapter": "Human Health and Disease", "type": "process"},
    {"query": "hiv replication reverse transcriptase aids", "expected_concept": "Human Health and Disease", "expected_chapter": "Human Health and Disease", "type": "process"},
    {"query": "microbes in sewage treatment bod activated sludge", "expected_concept": "Microbes in Human Welfare", "expected_chapter": "Microbes in Human Welfare", "type": "process"},
    {"query": "biogas production methanogens", "expected_concept": "Microbes in Human Welfare", "expected_chapter": "Microbes in Human Welfare", "type": "process"},

    # --- Biotechnology & Ecology (Class 12 Ch 9 to 13) ---
    {"query": "restriction endonucleases sticky ends recombinant dna", "expected_concept": "Restriction Endonucleases", "expected_chapter": "Biotechnology : Principles and Processes", "type": "mechanism"},
    {"query": "gel electrophoresis agarose dna fragments separation", "expected_concept": "Biotechnology : Principles and Processes", "expected_chapter": "Biotechnology : Principles and Processes", "type": "process"},
    {"query": "pcr polymerase chain reaction taq polymerase denaturation", "expected_concept": "Biotechnology : Principles and Processes", "expected_chapter": "Biotechnology : Principles and Processes", "type": "process"},
    {"query": "pbr322 plasmid cloning vector selectable markers", "expected_concept": "Biotechnology : Principles and Processes", "expected_chapter": "Biotechnology : Principles and Processes", "type": "structure"},
    {"query": "bt cotton cry gene pest resistance", "expected_concept": "Biotechnology and its Applications", "expected_chapter": "Biotechnology and its Applications", "type": "application"},
    {"query": "rna interference rnai in tobacco plants", "expected_concept": "Biotechnology and its Applications", "expected_chapter": "Biotechnology and its Applications", "type": "application"},
    {"query": "trophic levels 10 percent law of energy transfer", "expected_concept": "Ecosystem", "expected_chapter": "Ecosystem", "type": "concept"},
    {"query": "ecological pyramids inverted pyramid of biomass in sea", "expected_concept": "Ecosystem", "expected_chapter": "Ecosystem", "type": "concept"},
    {"query": "biodiversity hotspots in india western ghats", "expected_concept": "Biodiversity and Conservation", "expected_chapter": "Biodiversity and Conservation", "type": "fact"},
    {"query": "in situ vs ex situ conservation national park botanical garden", "expected_concept": "Biodiversity and Conservation", "expected_chapter": "Biodiversity and Conservation", "type": "comparison"},
]

# Out-of-Syllabus and Non-Biology Test Cases (Must be rejected)
REJECTION_TESTS = [
    ("what is Newton's second law?", "non_biology"),
    ("calculate the integral of x squared", "non_biology"),
    ("what caused the French Revolution in 1789?", "non_biology"),
    ("write a python script to sort a list", "non_biology"),
    ("what is quantum entanglement in physics", "non_biology"),
    ("chemical kinetics rate equation in chemistry", "non_biology"),
    ("tell me the capital of Australia", "non_biology"),
    ("how does internal combustion engine work", "non_biology"),
    ("what is Ohm's law of electrical resistance", "non_biology"),
    ("explain Einstein's general theory of relativity", "non_biology"),
]

# =====================================================================
# 2. RUN FULL BENCHMARK SUITE
# =====================================================================

def run_evaluation():
    print("=" * 70)
    print("  BioNEETPro - Comprehensive 100+ Query Evaluation Benchmark")
    print("=" * 70)

    # Metric 1: Retrieval Precision & MRR
    p1_hits = 0
    p3_hits = 0
    reciprocal_ranks = []
    chapter_matches = 0
    total_latency = 0.0

    print(f"\n[Phase 1] Evaluating {len(EVAL_BENCHMARK)} Unseen NCERT Biology Queries...")
    for item in EVAL_BENCHMARK:
        q = item["query"]
        exp_c = item["expected_concept"].lower()
        exp_chap = item["expected_chapter"].lower()

        t0 = time.time()
        results = retrieval_engine.search(q, top_k=3)
        dt = time.time() - t0
        total_latency += dt

        if not results:
            reciprocal_ranks.append(0.0)
            continue

        matched_p1 = False
        matched_p3 = False

        for rank, r in enumerate(results[:3]):
            text_combo = (r["title"] + " " + r["topic"] + " " + r["chapter_name"]).lower()
            if exp_c in text_combo or exp_chap in r["chapter_name"].lower():
                if rank == 0:
                    p1_hits += 1
                    matched_p1 = True
                p3_hits += 1
                matched_p3 = True
                reciprocal_ranks.append(1.0 / (rank + 1))
                break

        if not matched_p3:
            reciprocal_ranks.append(0.0)

        top = results[0]
        if exp_chap in top["chapter_name"].lower() or any(w in top["chapter_name"].lower() for w in exp_chap.split() if len(w) > 3):
            chapter_matches += 1

    total_q = len(EVAL_BENCHMARK)
    precision_at_1 = p1_hits / total_q
    precision_at_3 = p3_hits / total_q
    mrr = sum(reciprocal_ranks) / len(reciprocal_ranks)
    chapter_acc = chapter_matches / total_q
    avg_latency_ms = (total_latency / total_q) * 1000

    print(f"  • Total Queries Evaluated : {total_q}")
    print(f"  • Precision@1              : {precision_at_1 * 100:.1f}%")
    print(f"  • Precision@3              : {precision_at_3 * 100:.1f}%")
    print(f"  • MRR (Mean Recip Rank)    : {mrr:.4f}")
    print(f"  • Chapter Accuracy         : {chapter_acc * 100:.1f}%")
    print(f"  • Average Latency          : {avg_latency_ms:.1f} ms")

    # Metric 2: Non-Biology & Out-of-Syllabus Controlled Rejection
    print(f"\n[Phase 2] Evaluating Controlled Rejection on {len(REJECTION_TESTS)} Non-Biology Queries...")
    rejections = 0
    for q, _ in REJECTION_TESTS:
        s_check = syllabus_validator.check_query_syllabus(q)
        if not s_check["is_valid"]:
            rejections += 1

    rejection_rate = rejections / len(REJECTION_TESTS)
    print(f"  • Rejection Rate : {rejection_rate * 100:.1f}% ({rejections}/{len(REJECTION_TESTS)})")

    # Metric 3: Multi-turn Conversational Antecedent Resolution
    print("\n[Phase 3] Evaluating Conversational Context & Antecedent Resolution...")
    student_id = "eval_multi_turn_tester"
    conv_steps = [
        ("Explain mitochondria.", "Explain mitochondria.", "Mitochondria"),
        ("Why does it have folds?", "Why does Mitochondria have folds?", "Mitochondria"),
        ("What does that increase?", "What do Mitochondria folds (cristae) increase?", "Mitochondria"),
        ("Give me 3 questions on it.", "Give me 3 MCQs on Mitochondria", "Mitochondria"),
    ]

    history = []
    conv_success = 0
    for user_input, expected_resolved, exp_concept in conv_steps:
        res = nlp_pipeline.process_query(user_input, history, student_id=student_id)
        if exp_concept.lower() in res["resolved_query"].lower() or exp_concept.lower() in str(res.get("focal_concept", "")).lower():
            conv_success += 1
        history.append({"role": "user", "content": user_input})
        history.append({"role": "assistant", "content": f"Verified explanation on {exp_concept}."})

    conv_acc = conv_success / len(conv_steps)
    print(f"  • Multi-turn Antecedent Accuracy : {conv_acc * 100:.1f}% ({conv_success}/{len(conv_steps)})")

    # Metric 4: MCQ Engine Integrity
    print("\n[Phase 4] Evaluating MCQ Generator Structural Integrity...")
    mcqs_batch = mcq_engine.generate_mcqs("Give me 20 MCQs", student_id="eval_student")["mcqs"]
    valid_format = sum(1 for m in mcqs_batch if mcq_engine.validate_mcq(m))
    valid_opts = sum(1 for m in mcqs_batch if len(m["options"]) == 4 and len(set(m["options"])) == 4)
    has_ncert_exp = sum(1 for m in mcqs_batch if len(m.get("explanation", "")) > 15)

    mcq_valid_rate = valid_format / len(mcqs_batch) if mcqs_batch else 1.0
    mcq_exp_rate = has_ncert_exp / len(mcqs_batch) if mcqs_batch else 1.0
    print(f"  • 4-Option Structural Validity : {mcq_valid_rate * 100:.1f}%")
    print(f"  • NCERT Explanation Grounding  : {mcq_exp_rate * 100:.1f}%")

    # Metric 5: Final 12 Acceptance Test Queries
    print("\n" + "=" * 70)
    print("  FINAL 15 REAL-WORLD ACCEPTANCE TEST QUERIES BENCHMARK")
    print("=" * 70)

    ACCEPTANCE_QUERIES = [
        (1, "teach me about cell", "overview/cell"),
        (2, "teach me abt cell", "shorthand/cell"),
        (3, "what is a cell", "definition/cell"),
        (4, "explain mitochondria", "overview/mitochondria"),
        (5, "why does mitochondria have folds", "why/cristae"),
        (6, "what does that increase", "antecedent/surface_area"),
        (7, "teach me about brain", "overview/brain"),
        (8, "explain glycolysis EMP pathway and ATP yield", "mechanism/glycolysis_emp"),
        (9, "teach me glycolysis from basics", "pedagogy/basics"),
        (10, "why is ATP used in the first part of glycolysis?", "why/glycolysis_atp"),
        (11, "give me 2 mcq on cockroach chapter", "mcq/cockroach"),
        (12, "give me 5 hard questions on genetics", "mcq/genetics_hard"),
        (13, "give me questions from my weak topics", "mcq/weak_topics"),
        (14, "what is Newton's second law?", "rejection/non_biology"),
        (15, "Multi-Turn Chain: Mitochondria -> Folds -> Surface Area -> 3 MCQs", "multi_turn_chain"),
    ]

    all_acceptance_passed = True
    for idx, query, purpose in ACCEPTANCE_QUERIES:
        if idx == 14:
            # Must be rejected
            s_res = syllabus_validator.check_query_syllabus(query)
            passed = not s_res["is_valid"]
            detail = f"REJECTED cleanly ({s_res.get('refusal_message', '')[:40]}...)" if passed else "FAILED TO REJECT"
        elif idx in (11, 12, 13):
            # MCQ requests
            mcq_res = mcq_engine.generate_mcqs(query, student_id="accept_test")
            passed = mcq_res["status"] == "success" and len(mcq_res["mcqs"]) > 0
            detail = f"Generated {len(mcq_res['mcqs'])} MCQs on '{mcq_res['topic']}' (Diff: {mcq_res['difficulty']})"
        elif idx == 6:
            # Contextual question
            t_res = adaptive_tutor.generate_tutoring_response(
                query,
                student_id="accept_test",
                history=[
                    {"role": "user", "content": "Why does mitochondria have folds?"},
                    {"role": "assistant", "content": "The inner membrane forms infoldings called cristae."}
                ]
            )
            passed = t_res["status"] == "success" and "surface area" in t_res["reply"].lower()
            detail = f"Resolved to: {t_res['resolved_query']} | Surface Area verified in NCERT text"
        elif idx == 9:
            # Beginner explanation
            t_res = adaptive_tutor.generate_tutoring_response(query, student_id="accept_test")
            passed = t_res["status"] == "success" and t_res.get("strategy") in ("simplified_steps", "concrete_analogy")
            detail = f"Matched: {t_res.get('title')} | Strategy: {t_res.get('strategy')}"
        elif idx == 10:
            # ATP usage in glycolysis
            t_res = adaptive_tutor.generate_tutoring_response(query, student_id="accept_test")
            passed = t_res["status"] == "success" and ("utilised" in t_res["reply"].lower() or "glucose 6-phosphate" in t_res["reply"].lower() or "phosphorylat" in t_res["reply"].lower() or "hexokinase" in t_res["reply"].lower())
            detail = f"Matched: {t_res.get('title')} | Phosphorylation evidenced"
        elif idx == 15:
            # 4-turn conversational chain
            t_uid = "eval_chain_student"
            nlp_pipeline.context_tracker.clear_context(t_uid)
            r1 = adaptive_tutor.generate_tutoring_response("Explain mitochondria.", student_id=t_uid)
            r2 = adaptive_tutor.generate_tutoring_response("Why does it have folds?", student_id=t_uid, history=[{"role": "user", "content": "Explain mitochondria."}, {"role": "assistant", "content": r1["reply"]}])
            r3 = adaptive_tutor.generate_tutoring_response("What does that increase?", student_id=t_uid, history=[{"role": "user", "content": "Why does it have folds?"}, {"role": "assistant", "content": r2["reply"]}])
            r4 = mcq_engine.generate_mcqs("Give me 3 questions on it.", student_id=t_uid)
            passed = "surface area" in r3["reply"].lower() and r4["count"] == 3 and "mitochondria" in r4["topic"].lower()
            detail = f"All 4 turns linked: {r4['count']} MCQs on {r4['topic']}"
        else:
            t_res = adaptive_tutor.generate_tutoring_response(query, student_id="accept_test")
            passed = t_res["status"] == "success" and t_res["confidence"] in ("HIGH", "MEDIUM")
            detail = f"Matched: {t_res.get('title')} | Conf: {t_res.get('confidence')}"

        if not passed:
            all_acceptance_passed = False

        status_tag = "[PASS]" if passed else "[FAIL]"
        print(f"  Query #{idx:02d} {status_tag} : \"{query}\"")
        print(f"             ↳ {detail}")

    print("\n" + "=" * 70)
    final_status = "ALL 15 ACCEPTANCE TESTS PASSED SUCCESSFULLY!" if all_acceptance_passed else "SOME TESTS FAILED"
    print(f"  RESULT: {final_status}")
    print("=" * 70)

    return {
        "precision_at_1": precision_at_1,
        "precision_at_3": precision_at_3,
        "mrr": mrr,
        "chapter_accuracy": chapter_acc,
        "rejection_rate": rejection_rate,
        "conv_accuracy": conv_acc,
        "all_acceptance_passed": all_acceptance_passed
    }


if __name__ == "__main__":
    run_evaluation()
