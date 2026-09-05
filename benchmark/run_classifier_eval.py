#!/usr/bin/env python3
"""
BioNEET-Pro Classifier Evaluation Script
Runs the 6-class content classifier against benchmark datasets
and computes accuracy, macro precision/recall/F1, confusion matrix,
average/P95 latency.
"""

import json
import time
import sys
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Any

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from content_classifier import content_classifier

BENCHMARK_DIR = Path(__file__).resolve().parent
CLASSIFIER_DATASET = BENCHMARK_DIR / "classifier_dataset.json"
ADVERSARIAL_DATASET = BENCHMARK_DIR / "adversarial_dataset.json"
RESULTS_FILE = BENCHMARK_DIR / "results.json"
RESULTS_MD_FILE = BENCHMARK_DIR / "RESULTS.md"

CLASSES = [
    "Academic",
    "Educational-Sensitive",
    "Off-Topic",
    "Inappropriate",
    "Harmful",
    "Prompt-Injection",
]


def load_dataset(path: Path) -> List[Dict[str, Any]]:
    """Load dataset from JSON file."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def evaluate_dataset(dataset: List[Dict[str, Any]], name: str) -> Dict[str, Any]:
    """Evaluate classifier on a dataset."""
    print(f"\nEvaluating on {name} ({len(dataset)} samples)...")
    
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
        result = content_classifier.classify(query)
        latency_ms = (time.perf_counter() - start) * 1000
        
        predicted = result["classification"]
        
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
                "predicted": predicted,
                "confidence": result["confidence"],
                "scores": result["scores"]
            })
        
        if (i + 1) % 100 == 0:
            print(f"  Processed {i + 1}/{len(dataset)}")
    
    # Compute metrics
    accuracy = sum(1 for t, p in zip(y_true, y_pred) if t == p) / len(y_true)
    
    # Per-class precision, recall, F1
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
    
    # Latency stats
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
        "errors": errors[:20],  # Top 20 errors
    }


def print_results_table(results: Dict[str, Any]):
    """Print results in a formatted table."""
    print(f"\n{'='*70}")
    print(f"RESULTS: {results['dataset']}")
    print(f"{'='*70}")
    print(f"Total Samples: {results['total_samples']}")
    print(f"Accuracy:      {results['accuracy']:.4f}")
    print(f"Macro Precision: {results['macro_precision']:.4f}")
    print(f"Macro Recall:    {results['macro_recall']:.4f}")
    print(f"Macro F1:        {results['macro_f1']:.4f}")
    print(f"Avg Latency:     {results['avg_latency_ms']:.2f} ms")
    print(f"P95 Latency:     {results['p95_latency_ms']:.2f} ms")
    print(f"Errors:          {results['error_count']}")
    
    print("\nPer-Class Metrics:")
    print(f"{'Class':<25} {'Precision':>10} {'Recall':>10} {'F1':>10} {'Support':>10}")
    print("-" * 65)
    for cls in CLASSES:
        support = sum(results["confusion_matrix"][cls].values())
        print(f"{cls:<25} {results['per_class_precision'][cls]:>10.4f} {results['per_class_recall'][cls]:>10.4f} {results['per_class_f1'][cls]:>10.4f} {support:>10}")
    
    print("\nConfusion Matrix:")
    print(f"{'True\\Pred':<25}", end="")
    for cls in CLASSES:
        print(f"{cls[:10]:>10}", end="")
    print()
    print("-" * (25 + 10 * len(CLASSES)))
    for true_cls in CLASSES:
        print(f"{true_cls:<25}", end="")
        for pred_cls in CLASSES:
            print(f"{results['confusion_matrix'][true_cls][pred_cls]:>10}", end="")
        print()


def write_results_md(main_results: Dict[str, Any], adv_results: Dict[str, Any], keyword_baseline: Dict[str, Any] = None):
    """Write results to markdown file in paper table format."""
    with open(RESULTS_MD_FILE, "w", encoding="utf-8") as f:
        f.write("# BioNEET-Pro Content Classifier Evaluation Results\n\n")
        f.write(f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        # Main dataset results
        f.write("## Main Classifier Dataset (~600 samples)\n\n")
        f.write("| Metric | Value |\n")
        f.write("|--------|-------|\n")
        f.write(f"| Accuracy | {main_results['accuracy']:.4f} |\n")
        f.write(f"| Macro Precision | {main_results['macro_precision']:.4f} |\n")
        f.write(f"| Macro Recall | {main_results['macro_recall']:.4f} |\n")
        f.write(f"| Macro F1 | {main_results['macro_f1']:.4f} |\n")
        f.write(f"| Avg Latency (ms) | {main_results['avg_latency_ms']:.2f} |\n")
        f.write(f"| P95 Latency (ms) | {main_results['p95_latency_ms']:.2f} |\n\n")
        
        f.write("### Per-Class Metrics\n\n")
        f.write("| Class | Precision | Recall | F1 | Support |\n")
        f.write("|-------|-----------|--------|-----|---------|\n")
        for cls in CLASSES:
            support = sum(main_results["confusion_matrix"][cls].values())
            f.write(f"| {cls} | {main_results['per_class_precision'][cls]:.4f} | {main_results['per_class_recall'][cls]:.4f} | {main_results['per_class_f1'][cls]:.4f} | {support} |\n")
        f.write("\n")
        
        f.write("### Confusion Matrix\n\n")
        f.write("| True \\ Predicted | " + " | ".join(cls[:10] for cls in CLASSES) + " |\n")
        f.write("|" + "---|" * (len(CLASSES) + 1) + "\n")
        for true_cls in CLASSES:
            row = [str(main_results["confusion_matrix"][true_cls][pred_cls]) for pred_cls in CLASSES]
            f.write(f"| {true_cls} | " + " | ".join(row) + " |\n")
        f.write("\n")
        
        # Adversarial results
        f.write("## Adversarial Dataset (60 edge cases)\n\n")
        f.write("| Metric | Value |\n")
        f.write("|--------|-------|\n")
        f.write(f"| Accuracy | {adv_results['accuracy']:.4f} |\n")
        f.write(f"| Macro Precision | {adv_results['macro_precision']:.4f} |\n")
        f.write(f"| Macro Recall | {adv_results['macro_recall']:.4f} |\n")
        f.write(f"| Macro F1 | {adv_results['macro_f1']:.4f} |\n")
        f.write(f"| Avg Latency (ms) | {adv_results['avg_latency_ms']:.2f} |\n")
        f.write(f"| P95 Latency (ms) | {adv_results['p95_latency_ms']:.2f} |\n\n")
        
        f.write("### Per-Class Metrics (Adversarial)\n\n")
        f.write("| Class | Precision | Recall | F1 | Support |\n")
        f.write("|-------|-----------|--------|-----|---------|\n")
        for cls in CLASSES:
            support = sum(adv_results["confusion_matrix"][cls].values())
            f.write(f"| {cls} | {adv_results['per_class_precision'][cls]:.4f} | {adv_results['per_class_recall'][cls]:.4f} | {adv_results['per_class_f1'][cls]:.4f} | {support} |\n")
        f.write("\n")
        
        f.write("### Confusion Matrix (Adversarial)\n\n")
        f.write("| True \\ Predicted | " + " | ".join(cls[:10] for cls in CLASSES) + " |\n")
        f.write("|" + "---|" * (len(CLASSES) + 1) + "\n")
        for true_cls in CLASSES:
            row = [str(adv_results["confusion_matrix"][true_cls][pred_cls]) for pred_cls in CLASSES]
            f.write(f"| {true_cls} | " + " | ".join(row) + " |\n")
        f.write("\n")
        
        # Keyword baseline comparison
        if keyword_baseline:
            f.write("## Keyword Baseline Comparison\n\n")
            f.write("| Metric | Our Classifier | Keyword Baseline |\n")
            f.write("|--------|----------------|------------------|\n")
            f.write(f"| Accuracy | {main_results['accuracy']:.4f} | {keyword_baseline.get('accuracy', 0):.4f} |\n")
            f.write(f"| Macro Precision | {main_results['macro_precision']:.4f} | {keyword_baseline.get('macro_precision', 0):.4f} |\n")
            f.write(f"| Macro Recall | {main_results['macro_recall']:.4f} | {keyword_baseline.get('macro_recall', 0):.4f} |\n")
            f.write(f"| Macro F1 | {main_results['macro_f1']:.4f} | {keyword_baseline.get('macro_f1', 0):.4f} |\n\n")
        
        f.write("---\n\n")
        f.write("*Note: These are real measured numbers from the current implementation. ")
        f.write("They may differ from paper claims (99.33%/93.33%). ")
        f.write("Paper results should be corrected to match reality.*\n")


def main():
    print("BioNEET-Pro Classifier Evaluation")
    print("=" * 50)
    
    # Load datasets
    classifier_data = load_dataset(CLASSIFIER_DATASET)
    adversarial_data = load_dataset(ADVERSARIAL_DATASET)
    
    print(f"Loaded {len(classifier_data)} classifier samples")
    print(f"Loaded {len(adversarial_data)} adversarial samples")
    
    # Evaluate
    main_results = evaluate_dataset(classifier_data, "Main Classifier Dataset")
    adv_results = evaluate_dataset(adversarial_data, "Adversarial Dataset")
    
    # Print to console
    print_results_table(main_results)
    print_results_table(adv_results)
    
    # Load keyword baseline if available
    keyword_baseline = None
    baseline_path = BENCHMARK_DIR / "keyword_baseline_results.json"
    if baseline_path.exists():
        with open(baseline_path, "r") as f:
            keyword_baseline = json.load(f)
    
    # Write combined results
    combined = {
        "main_dataset": main_results,
        "adversarial_dataset": adv_results,
        "keyword_baseline": keyword_baseline,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    
    with open(RESULTS_FILE, "w", encoding="utf-8") as f:
        json.dump(combined, f, indent=2)
    
    write_results_md(main_results, adv_results, keyword_baseline)
    
    print(f"\nResults saved to {RESULTS_FILE}")
    print(f"Markdown report saved to {RESULTS_MD_FILE}")
    
    # Summary
    print(f"\n{'='*70}")
    print("SUMMARY")
    print(f"{'='*70}")
    print(f"Main Dataset Accuracy:  {main_results['accuracy']:.2%}")
    print(f"Adversarial Accuracy:   {adv_results['accuracy']:.2%}")
    print(f"Main Macro F1:          {main_results['macro_f1']:.4f}")
    print(f"Adversarial Macro F1:   {adv_results['macro_f1']:.4f}")
    print(f"Avg Latency:            {main_results['avg_latency_ms']:.2f} ms")
    print(f"P95 Latency:            {main_results['p95_latency_ms']:.2f} ms")


if __name__ == "__main__":
    main()