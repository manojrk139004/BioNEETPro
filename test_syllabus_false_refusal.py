from syllabus import syllabus_validator

# Test some NCERT biology terms that might be rejected
test_queries = [
    "What is the Haversian system in bone?",
    "Explain the photoperiodism in plants",
    "What is periderm in plant anatomy?",
    "Describe the juxtaglomerular apparatus function",
    "How does the countercurrent mechanism work in nephron?",
    "What is the chloride shift in blood?",
    "Explain the Bohr effect in oxygen transport",
    "What is the role of SA node in cardiac cycle?",
    "Describe the structure of nephron",
    "What is the Hatch-Slack pathway in C4 plants?",
    "Explain the Krebs cycle in mitochondria",
    "What is the function of guard cells in stomata?",
    "Describe the process of transpiration pull",
    "What is the significance of crossing over in meiosis?",
    "Explain the lac operon regulation in E. coli",
]

for q in test_queries:
    res = syllabus_validator.check_query_syllabus(q)
    status = "VALID" if res["is_valid"] else "REJECTED"
    reason = res.get("reason", "")
    matched = res.get("matched_keywords", [])
    print(f'{status} | {reason:25s} | matched: {matched[:3]} | Q: {q}')