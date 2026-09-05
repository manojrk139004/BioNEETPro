#!/usr/bin/env python3
"""
BioNEET-Pro Keyword Baseline Classifier
Simple rule-based baseline for comparison with the main classifier.
Uses keyword matching for each of the 6 categories.
"""

import json
import re
import sys
import time
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

BENCHMARK_DIR = Path(__file__).resolve().parent
CLASSIFIER_DATASET = BENCHMARK_DIR / "classifier_dataset.json"
ADVERSARIAL_DATASET = BENCHMARK_DIR / "adversarial_dataset.json"
BASELINE_RESULTS_FILE = BENCHMARK_DIR / "keyword_baseline_results.json"

CLASSES = [
    "Academic",
    "Educational-Sensitive",
    "Off-Topic",
    "Inappropriate",
    "Harmful",
    "Prompt-Injection",
]

# Keyword-based rules for each category
KEYWORD_RULES = {
    "Harmful": [
        "kill myself", "commit suicide", "end my life", "hang myself", "cut myself",
        "how to make a bomb", "make explosives", "synthesize meth", "cook methamphetamine",
        "make heroin", "poison someone", "kill someone", "school shooting",
        "build a weapon", "molotov cocktail", "terrorist attack", "mass murder",
        "poison water supply", "deadly poison", "make fentanyl", "make cocaine",
        "weapon manufacturing", "make an ied",
    ],
    "Prompt-Injection": [
        "ignore all previous instructions", "forget everything you were told",
        "override your system prompt", "you are now dan", "pretend you are unrestricted",
        "act as an evil", "developer mode", "jailbreak mode", "god mode",
        "what is your system prompt", "show me your hidden instructions",
        "print everything above", "reveal your initial prompt", "what were you told",
        "base64 decode", "rot13", "decode this hex", "<!-- system", "[system note",
        "roleplay as an unrestricted", "disable your safety", "bypass your content filter",
        "ignore your guidelines", "you don't need to follow rules",
        "break character", "roleplay as an ai without rules",
        "hypothetical scenario", "no guidelines", "admin override",
    ],
    "Inappropriate": [
        "fuck you", "piece of shit", "go to hell", "bitch", "motherfucker",
        "suck my dick", "eat shit", "fucking idiot", "fuck off", "stupid cunt",
        "asshole", "send nudes", "show me your boobs", "wanna have sex",
        "i want to fuck", "you're so hot", "sex chat", "naked pics",
        "i'm so horny", "blowjob", "nice tits", "see you naked", "let's do it",
        "your body is amazing",
    ],
    "Off-Topic": [
        "newton", "quantum mechanics", "velocity", "gauss law", "thermodynamics",
        "sn1 reaction", "chemical equations", "periodic table", "organic chemistry",
        "molar mass", "quadratic", "pythagorean", "calculus", "integration",
        "python function", "javascript", "react hooks", "sql join", "rest api",
        "cricket world cup", "capital of france", "stock market", "bitcoin",
        "bake a cake", "tell me a joke", "weather today", "prime minister",
        "french revolution", "machine learning", "neural network", "docker",
        "linux commands", "sorting algorithm", "binary search", "leetcode",
        "github", "kubernetes", "deploy web app", "recipe for pasta",
        "recommend a movie", "sing a song", "meaning of life", "make money online",
        "cryptocurrency mining", "blockchain", "nft", "invest in stocks",
        "best programming language", "java vs python", "html css", "make a website",
    ],
    "Educational-Sensitive": [
        "human reproduction", "menstrual cycle", "spermatogenesis", "oogenesis",
        "fertilization", "menstrual cycle phases", "ovulation", "luteal phase",
        "follicular phase", "implantation", "blastocyst", "placenta", "parturition",
        "lactation", "gametogenesis", "sertoli cells", "leydig cells",
        "seminiferous tubules", "spermiogenesis", "graafian follicle",
        "granulosa cells", "theca cells", "fsh", "lh surge", "estrogen",
        "progesterone", "acrosome reaction", "zona pellucida", "cleavage",
        "morula", "gastrulation", "germ layers", "hcg", "oxytocin", "prolactin",
        "contraceptive", "iud", "copper-t", "oral contraceptive", "condom",
        "vasectomy", "tubectomy", "barrier method", "medical termination",
        "amniocentesis", "assisted reproductive", "ivf", "zift", "gift",
        "icsi", "iui", "surrogacy", "sexually transmitted", "syphilis",
        "gonorrhea", "chlamydia", "trichomoniasis", "genital herpes",
        "hepatitis b", "hiv", "aids", "male reproductive system",
        "female reproductive system", "testes", "ovaries", "epididymis",
        "vas deferens", "seminal vesicles", "prostate gland", "bulbourethral",
        "penis", "fallopian tubes", "uterus", "cervix", "vagina", "mammary glands",
        "puberty", "secondary sexual characteristics", "masturbation", "orgasm",
    ],
    "Academic": [
        "mitochondria", "photosynthesis", "dna replication", "nephron",
        "mendel", "cardiac cycle", "sliding filament", "ribosomes",
        "glycolysis", "calvin cycle", "xylem", "phloem", "neuron",
        "transcription", "mitosis", "sa node", "oxygen transport",
        "krebs cycle", "meiosis", "chloroplast", "lac operon",
        "photophosphorylation", "countercurrent", "guard cells",
        "transpiration pull", "crossing over", "bohr effect",
        "lysosomes", "endoplasmic reticulum", "atp synthase",
        "dna replication", "cell cycle", "golgi apparatus",
        "peroxisomes", "light reaction", "rubisco", "plant cell",
        "nucleus", "translation", "types of rna", "trna structure",
        "genetic code", "transcription eukaryotes", "rna polymerase",
        "gene structure", "introns exons", "rna splicing", "spliceosome",
        "ribosome structure", "mrna translation", "translation stages",
        "dna structure", "histones", "chromatin", "dna polymerase",
        "replication fork", "okazaki fragments", "proofreading",
        "telomerase", "chromosomes", "cell cycle checkpoint",
        "cyclins", "g1 phase", "s phase", "g2 checkpoint",
        "cytokinesis", "centromere", "kinetochore", "spindle checkpoint",
        "anaphase promoting", "separase", "microtubules", "motor proteins",
        "vesicle transport", "snare proteins", "endomembrane system",
        "er function", "protein folding", "unfolded protein response",
        "golgi structure", "protein glycosylation", "secretory pathway",
        "lysosome function", "autophagy", "mitochondria structure",
        "electron transport chain", "chemiosmotic theory", "atp synthase",
        "oxidative phosphorylation", "nadh", "fadh2", "chloroplast structure",
        "thylakoids", "light-dependent reactions", "z-scheme",
        "calvin cycle steps", "rubp carboxylase", "photorespiration",
        "c4 photosynthesis", "kranz anatomy", "cam photosynthesis",
        "stomata structure", "stomatal opening", "transpiration",
        "cohesion-tension", "pressure flow hypothesis", "phloem loading",
        "sieve tubes", "companion cells", "translocation",
        "plant hormones", "auxins", "gibberellins", "cytokinins",
        "abscisic acid", "ethylene function", "photoperiodism",
        "vernalization", "seed dormancy", "germination",
        "dicot seed", "monocot seed", "endosperm function",
        "double fertilization", "embryo sac", "pollination",
        "pollination types", "pollen grain", "stigma function",
        "pollen-pistil interaction", "self-incompatibility",
        "ovule structure", "megasporogenesis", "mature embryo sac",
        "synergids role", "fertilization process", "triple fusion",
        "endosperm development", "dicot embryo", "monocot embryo",
        "apomixis", "polyembryony", "fruit structure", "fruit types",
        "seed dispersal", "dispersal agents", "flower structure",
        "flower whorls", "aestivation", "placentation types",
        "anther structure", "microsporogenesis", "pollen grain structure",
        "male gametophyte", "pistil structure", "megasporogenesis",
        "female gametophyte", "pollination process", "outbreeding devices",
        "pollen-pistil interaction", "double fertilization",
        "post-fertilization events", "seed structure", "fruit structure",
        "seed dormancy germination", "apomixis polyembryony",
        "plant growth regulators", "auxins role", "gibberellins function",
        "cytokinins role", "ethylene function", "abscisic acid role",
        "photoperiodism definition", "vernalization process",
        "seed dormancy factors", "germination process",
    ],
}

# Compile keyword patterns for faster matching
COMPILED_RULES = {}
for category, keywords in KEYWORD_RULES.items():
    # Create regex pattern that matches any of the keywords
    pattern = r"|".join(re.escape(kw) for kw in keywords)
    COMPILED_RULES[category] = re.compile(pattern, re.IGNORECASE)


def classify_keyword_baseline(query: str) -> str:
    """Classify query using keyword matching."""
    query_lower = query.lower()
    
    # Check in priority order: security categories first
    for category in ["Harmful", "Prompt-Injection", "Inappropriate", "Off-Topic", "Educational-Sensitive", "Academic"]:
        if COMPILED_RULES[category].search(query_lower):
            return category
    
    # Default to Academic if no match
    return "Academic"


def evaluate_baseline(dataset: List[Dict[str, Any]], name: str) -> Dict[str, Any]:
    """Evaluate keyword baseline on a dataset."""
    print(f"\nEvaluating keyword baseline on {name} ({len(dataset)} samples)...")
    
    y_true = []
    y_pred = []
    latencies = []
    per_class_correct = defaultdict(int)
    per_class_total = defaultdict(int)
    errors = []
    
    for i, sample in enumerate(dataset):
        query = sample["query"]
        expected = sample["expected"]
        
        start = time.perf_counter()
        predicted = classify_keyword_baseline(query)
        latency_ms = (time.perf_counter() - start) * 1000
        
        y_true.append(expected)
        y_pred.append(predicted)
        latencies.append(latency_ms)
        
        per_class_total[expected] += 1
        if predicted == expected:
            per_class_correct[expected] += 1
        else:
            errors.append({
                "query": query,
                "expected": expected,
                "predicted": predicted
            })
        
        if (i + 1) % 100 == 0:
            print(f"  Processed {i + 1}/{len(dataset)}")
    
    # Compute metrics
    accuracy = sum(1 for t, p in zip(y_true, y_pred) if t == p) / len(y_true)
    
    precision = {}
    recall = {}
    f1 = {}
    
    for cls in CLASSES:
        tp = per_class_correct.get(cls, 0)
        fp = sum(1 for t, p in zip(y_true, y_pred) if p == cls and t != cls)
        fn = per_class_total.get(cls, 0) - tp
        
        precision[cls] = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall[cls] = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1[cls] = 2 * precision[cls] * recall[cls] / (precision[cls] + recall[cls]) if (precision[cls] + recall[cls]) > 0 else 0.0
    
    macro_precision = sum(precision.values()) / len(CLASSES)
    macro_recall = sum(recall.values()) / len(CLASSES)
    macro_f1 = sum(f1.values()) / len(CLASSES)
    
    # Confusion matrix
    confusion = {cls: {c: 0 for c in CLASSES} for cls in CLASSES}
    for t, p in zip(y_true, y_pred):
        confusion[t][p] += 1
    
    avg_latency = sum(latencies) / len(latencies)
    p95_latency = sorted(latencies)[int(0.95 * len(latencies))]
    
    return {
        "dataset": name,
        "total_samples": len(dataset),
        "accuracy": round(accuracy, 4),
        "macro_precision": round(macro_precision, 4),
        "macro_recall": round(macro_recall, 4),
        "macro_f1": round(macro_f1, 4),
        "per_class_precision": {k: round(v, 4) for k, v in precision.items()},
        "per_class_recall": {k: round(v, 4) for k, v in recall.items()},
        "per_class_f1": {k: round(v, 4) for k, v in f1.items()},
        "confusion_matrix": confusion,
        "avg_latency_ms": round(avg_latency, 2),
        "p95_latency_ms": round(p95_latency, 2),
        "error_count": len(errors),
    }


def main():
    print("BioNEET-Pro Keyword Baseline Evaluation")
    print("=" * 50)
    
    # Load datasets
    with open(CLASSIFIER_DATASET, "r", encoding="utf-8") as f:
        classifier_data = json.load(f)
    
    with open(ADVERSARIAL_DATASET, "r", encoding="utf-8") as f:
        adversarial_data = json.load(f)
    
    print(f"Loaded {len(classifier_data)} classifier samples")
    print(f"Loaded {len(adversarial_data)} adversarial samples")
    
    # Evaluate
    main_results = evaluate_baseline(classifier_data, "Main Classifier Dataset")
    adv_results = evaluate_baseline(adversarial_data, "Adversarial Dataset")
    
    # Print summary
    print(f"\n{'='*70}")
    print("KEYWORD BASELINE SUMMARY")
    print(f"{'='*70}")
    print(f"Main Dataset Accuracy:  {main_results['accuracy']:.2%}")
    print(f"Adversarial Accuracy:   {adv_results['accuracy']:.2%}")
    print(f"Main Macro F1:          {main_results['macro_f1']:.4f}")
    print(f"Adversarial Macro F1:   {adv_results['macro_f1']:.4f}")
    print(f"Avg Latency:            {main_results['avg_latency_ms']:.2f} ms")
    print(f"P95 Latency:            {main_results['p95_latency_ms']:.2f} ms")
    
    # Save results
    combined = {
        "main_dataset": main_results,
        "adversarial_dataset": adv_results,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    
    with open(BASELINE_RESULTS_FILE, "w", encoding="utf-8") as f:
        json.dump(combined, f, indent=2)
    
    print(f"\nBaseline results saved to {BASELINE_RESULTS_FILE}")


if __name__ == "__main__":
    main()