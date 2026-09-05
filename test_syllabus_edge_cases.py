from syllabus import syllabus_validator

# Test edge cases that might be falsely rejected
test_queries = [
    "What is the significance of vascular cambium?",
    "Explain the cohesion-tension theory",
    "What is the role of phytochrome in flowering?",
    "Describe the structure of sieve tube elements",
    "How does the Munch pressure flow hypothesis work?",
    "What is the function of companion cells in phloem?",
    "Explain the root pressure mechanism in xylem",
    "What is the significance of double fertilization?",
    "Describe the structure of embryo sac",
    "What is the role of tapetum in anther development?",
    "Explain the process of microsporogenesis",
    "What is the function of endosperm in seed development?",
    "Describe the structure of pollen grain",
    "What is the significance of apomixis in plants?",
    "Explain the process of spermatogenesis in humans",
    "What is the role of Sertoli cells in testes?",
    "Describe the structure of Graafian follicle",
    "What is the function of corpus luteum?",
    "Explain the menstrual cycle phases",
    "What is the significance of LH surge in ovulation?",
]

for q in test_queries:
    res = syllabus_validator.check_query_syllabus(q)
    status = "VALID" if res["is_valid"] else "REJECTED"
    reason = res.get("reason", "")
    matched = res.get("matched_keywords", [])
    print(f'{status} | {reason:25s} | matched: {matched[:3]} | Q: {q}')