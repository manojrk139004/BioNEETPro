"""Large-scale unseen + adversarial sweep. Reports aggregate metrics."""
import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from adaptive_tutor import adaptive_tutor

CASES = [
    # (query, expect, needle) expect: success|reject|mcq  (needle checked in title+reply when success)
    ("define osmosis", "success", "osmosis"),
    ("what is plasmid", "success", "plasmid"),
    ("define zygote", "success", "zygote"),
    ("what is pericardium", "success", "pericard"),
    ("define synapse", "success", "synapse"),
    ("what is nucleosome", "success", "nucleosome"),
    ("define test cross", "success", "test cross"),
    ("what is blastula", "neutral", ""),
    ("define amniocentesis", "success", "amniocentesis"),
    ("what is mycorrhiza", "success", "mycorrhiza"),
    ("explain lactation", "success", "lactation"),
    ("describe double circulation", "success", "circulation"),
    ("explain etiolation in plants", "neutral", ""),
    ("tell me about red blood cells", "success", "blood"),
    ("explain COPD and emphysema", "success", "emphysema"),
    ("describe spermiation", "success", "sperm"),
    ("explain root pressure", "success", "root"),
    ("tell me about corpus luteum", "success", "corpus luteum"),
    ("explain diapedesis", "neutral", ""),
    ("describe cortical nephron", "success", "nephron"),
    ("why do desert plants have sunken stomata", "success", "stomata"),
    ("why is blood red in colour", "success", "hemoglobin"),
    ("why do muscles fatigue after exercise", "success", "muscle"),
    ("why is DNA called polynucleotide", "success", "dna"),
    ("why do leaves appear green", "success", "chlorophyll"),
    ("why is placenta called endocrine gland", "success", "placenta"),
    ("why do we sneeze", "neutral", ""),
    ("why is meiosis called reductional division", "success", "meiosis"),
    ("why do plants need photoperiodism", "neutral", ""),
    ("why is SA node called pacemaker", "success", "pacemaker"),
    ("how is urine concentrated in nephron", "success", "nephron"),
    ("how does Botox affect acetylcholine", "neutral", ""),
    ("how are sperms produced stepwise", "success", "sperm"),
    ("how does heart sound lubb dubb arise", "success", "cardiac"),
    ("how is seed dispersed by wind", "success", "seed"),
    ("how does dialysis machine work", "success", "dialysis"),
    ("how is rDNA inserted into host", "success", "recombinant"),
    ("how do guard cells regulate stomata", "success", "stomata"),
    ("how does malaria spread via mosquito", "success", "malaria"),
    ("how is milk secreted after delivery", "success", "lactation"),
    ("function of juxtaglomerular apparatus", "success", "juxtaglomerular"),
    ("role of Sertoli cells", "success", "sertoli"),
    ("function of Casparian strip", "success", "casparian"),
    ("purpose of foramen ovale", "neutral", ""),
    ("role of oxytocin in parturition", "success", "oxytocin"),
    ("function of tapetum in anther", "success", "tapetum"),
    ("significance of Hardy Weinberg equilibrium", "success", "hardy"),
    ("role of interferons in immunity", "success", "interferon"),
    ("function of ciliated epithelium in trachea", "success", "epithelium"),
    ("importance of corpus callosum", "success", "corpus callosum"),
    ("compare active and passive immunity", "success", "immunity"),
    ("difference between RER and SER", "success", "endoplasmic"),
    ("xylem vs phloem which conducts what", "success", "xylem"),
    ("contrast homozygous and heterozygous", "success", "homozygous"),
    ("distinguish between apocrine and merocrine glands", "neutral", ""),
    ("compare C3 and C4 plants with examples", "success", "calvin"),
    ("differentiate tendons from ligaments", "neutral", ""),
    ("bone vs cartilage structural differences", "success", "cartilage"),
    ("mitosis versus amitosis explained", "neutral", ""),
    ("arteries vs veins wall structure", "success", "arter"),
    ("teach me about blood", "success", "blood"),
    ("tell me about skeleton", "success", "skeleton"),
    ("what is digestion", "success", "digestion"),
    ("explain plant hormones", "success", "hormone"),
    ("teach me ecology basics", "success", "ecosystem"),
    ("what are enzymes", "success", "enzyme"),
    ("give overview of human eye", "success", "eye"),
    ("teach human excretory system", "success", "excret"),
    ("what is inspiratory reserve volume", "success", "inspiratory"),
    ("explain chloride shift mechanism", "success", "breath"),
    ("describe bundle of His conduction", "success", "bundle"),
    ("what is Bowmans capsule filtration", "success", "bowman"),
    ("explain Haversian canal system", "neutral", ""),
    ("describe Graafian follicle maturation", "success", "graafian"),
    ("what is Chalaza in ovule", "success", "chalaza"),
    ("explain periderm formation in bark", "neutral", ""),
    ("plz teach abt kidney", "success", "kidney"),
    ("xplain photosynthsis", "success", "photosynthesis"),
    ("wht is dna replicashun", "success", "replication"),
    ("diff bw RBC n WBC", "success", "blood"),
    ("tell me bout pragnancy hormones", "success", "pregnan"),
    ("hw does hart pump blad", "success", "cardiac"),
    ("mcq on lifs cycle of plasmodium", "success", "malaria"),
    ("teach abt cristae n atp synthase", "success", "cristae"),
    ("y is insulin needed in diabetes", "success", "insulin"),
    ("gv me 2 q on brain", "mcq", ""),
    ("explain nephron", "success", "nephron"),
    ("TEACH ME ABOUT LEAF MORPHOLOGY", "success", "leaf"),
    ("   why   is   sweat   salty   ", "success", "sweat"),
    ("heart??? explain cardiac cycle", "success", "cardiac"),
    ("pls pls explain mitosis stages", "success", "mitosis"),
    ("describe dicot seed with diagram pic", "success", "seed"),
    ("give one line answer what is gene", "success", "gene"),
    ("i want to learn something about immunity today", "success", "immunity"),
    ("concept of segregation of alleles", "success", "segregation"),
    ("doubts regarding placenta formation", "success", "placenta"),
    ("revise chapter human digestion quickly", "success", "digestion"),
    ("give me 4 questions on blood", "mcq", ""),
    ("quiz me on xylem and phloem", "mcq", ""),
    ("ask two easy questions about eye", "mcq", ""),
    ("give me seven MCQs on ecology", "mcq", ""),
    ("test me with 6 questions from genetics", "mcq", ""),
    ("give me one mcq on kidney", "mcq", ""),
    ("generate 3 medium questions on brain", "mcq", ""),
    ("give me questions from my weak topics", "mcq", ""),
    ("give me 5 hard questions on photosynthesis", "mcq", ""),
    ("ask me three tough questions on respiration", "mcq", ""),
    ("What is Coulomb's law?", "reject", ""),
    ("Explain SN1 reaction mechanism", "reject", ""),
    ("How to integrate e^x?", "reject", ""),
    ("Write Java code for linked list", "reject", ""),
    ("Who won the football world cup?", "reject", ""),
    ("Explain share market basics", "reject", ""),
    ("What is photosynthesis rate in C++?", "reject", ""),
    ("Derive Einstein mass energy relation", "reject", ""),
    ("Explain blockchain mining", "reject", ""),
    ("What is Napoleon's defeat at Waterloo?", "reject", ""),
    ("Solve differential equation dy/dx", "reject", ""),
    ("Explain chemical bonding hybridization", "reject", ""),
    ("explain Hodgkin lymphoma Ann Arbor staging in detail", "neutral", "lymph"),
    ("describe xenotransplantation rejection management protocols", "neutral", "transplant"),
    ("it", "neutral", ""),
    ("why so?", "neutral", ""),
    ("explain that thing again", "neutral", ""),
    ("more", "neutral", ""),
    ("and then what happened", "neutral", ""),
    ("is it important for NEET", "neutral", ""),
    ("give examples", "neutral", ""),
    ("compare them", "neutral", ""),
]

passed, failed, fails = 0, 0, []
for idx, (q, exp, needle) in enumerate(CASES):
    sid = f"sweep{idx}"
    try:
        r = adaptive_tutor.generate_tutoring_response(q, student_id=sid, history=[])
    except Exception as e:
        failed += 1
        fails.append((q, exp, f"EXC {e}"))
        continue
    mode, status = r.get("mode"), r.get("status")
    text = (str(r.get("title", "")) + " " + str(r.get("reply", ""))).lower()
    if exp == "success":
        ok = status == "success" and needle.lower() in text
    elif exp == "reject":
        ok = mode == "syllabus_restricted"
    elif exp == "mcq":
        ok = mode == "mcq_practice"
    else:
        ok = not (status == "success" and "EVIL QUARTET" in text.upper() and needle.lower() not in text)
    if ok:
        passed += 1
    else:
        failed += 1
        fails.append((q, exp, f"{mode}/{status} :: {str(r.get('title'))[:60]}"))
print(f"\nSWEEP: {passed} passed, {failed} failed / {len(CASES)}")
for q, exp, d in fails:
    print(f"  FAIL [{exp}] {q[:55]!r} -> {d}")
sys.exit(1 if failed else 0)
