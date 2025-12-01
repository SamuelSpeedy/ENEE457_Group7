#!/usr/bin/env python3
"""
Batch test malware/benign samples against the API and generate accuracy metrics.
"""

import requests
import os
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

API_URL = "http://localhost:8000/predict"
BASE_DIR = Path(__file__).parent
MALWARE_DIR = BASE_DIR / "malware_samples"
BENIGN_DIR = BASE_DIR / "benign_samples"


def test_file(filepath: Path, expected_label: str) -> dict:
    """Test a single file against the API."""
    try:
        with open(filepath, "rb") as f:
            response = requests.post(
                API_URL,
                files={"file": (filepath.name, f)},
                timeout=60
            )

        if response.status_code == 200:
            data = response.json()
            return {
                "file": filepath.name,
                "expected": expected_label,
                "predicted": data["label"],
                "confidence": data["confidence"],
                "correct": data["label"] == expected_label,
                "error": None
            }
        else:
            return {
                "file": filepath.name,
                "expected": expected_label,
                "predicted": None,
                "confidence": 0,
                "correct": False,
                "error": f"HTTP {response.status_code}"
            }
    except Exception as e:
        return {
            "file": filepath.name,
            "expected": expected_label,
            "predicted": None,
            "confidence": 0,
            "correct": False,
            "error": str(e)
        }


def main():
    results = []

    # Get all sample files
    malware_files = list(MALWARE_DIR.glob("*")) if MALWARE_DIR.exists() else []
    benign_files = list(BENIGN_DIR.glob("*")) if BENIGN_DIR.exists() else []

    print(f"Testing {len(malware_files)} malware samples and {len(benign_files)} benign samples...\n")

    # Test in parallel for speed
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = []

        for f in malware_files:
            if f.is_file():
                futures.append(executor.submit(test_file, f, "malicious"))

        for f in benign_files:
            if f.is_file():
                futures.append(executor.submit(test_file, f, "benign"))

        for i, future in enumerate(as_completed(futures)):
            result = future.result()
            results.append(result)

            status = "CORRECT" if result["correct"] else "WRONG"
            if result["error"]:
                status = f"ERROR: {result['error']}"

            print(f"[{i+1}/{len(futures)}] {result['file'][:40]:40} | "
                  f"Expected: {result['expected']:9} | "
                  f"Got: {str(result['predicted']):9} | "
                  f"Conf: {result['confidence']*100:5.1f}% | {status}")

    # Calculate metrics
    print("\n" + "="*80)
    print("RESULTS SUMMARY")
    print("="*80)

    total = len(results)
    correct = sum(1 for r in results if r["correct"])
    errors = sum(1 for r in results if r["error"])

    malware_results = [r for r in results if r["expected"] == "malicious" and not r["error"]]
    benign_results = [r for r in results if r["expected"] == "benign" and not r["error"]]

    true_positives = sum(1 for r in malware_results if r["predicted"] == "malicious")
    false_negatives = sum(1 for r in malware_results if r["predicted"] == "benign")
    true_negatives = sum(1 for r in benign_results if r["predicted"] == "benign")
    false_positives = sum(1 for r in benign_results if r["predicted"] == "malicious")

    print(f"\nTotal samples tested: {total}")
    print(f"Errors (couldn't process): {errors}")
    print(f"Successfully processed: {total - errors}")
    print(f"\nCorrect predictions: {correct}")
    print(f"Accuracy: {correct/(total-errors)*100:.1f}%" if total-errors > 0 else "N/A")

    print(f"\n--- Malware Detection ---")
    print(f"True Positives (malware detected as malware): {true_positives}")
    print(f"False Negatives (malware detected as benign): {false_negatives}")
    if len(malware_results) > 0:
        print(f"Recall/TPR: {true_positives/len(malware_results)*100:.1f}%")

    print(f"\n--- Benign Detection ---")
    print(f"True Negatives (benign detected as benign): {true_negatives}")
    print(f"False Positives (benign detected as malware): {false_positives}")
    if len(benign_results) > 0:
        print(f"Specificity/TNR: {true_negatives/len(benign_results)*100:.1f}%")

    # Precision and F1
    if true_positives + false_positives > 0:
        precision = true_positives / (true_positives + false_positives)
        print(f"\nPrecision: {precision*100:.1f}%")

        if len(malware_results) > 0:
            recall = true_positives / len(malware_results)
            f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
            print(f"F1 Score: {f1*100:.1f}%")

    # Average confidences
    mal_confs = [r["confidence"] for r in malware_results if r["predicted"]]
    ben_confs = [r["confidence"] for r in benign_results if r["predicted"]]

    if mal_confs:
        print(f"\nAvg confidence on malware: {sum(mal_confs)/len(mal_confs)*100:.1f}%")
    if ben_confs:
        print(f"Avg confidence on benign: {sum(ben_confs)/len(ben_confs)*100:.1f}%")


if __name__ == "__main__":
    main()
