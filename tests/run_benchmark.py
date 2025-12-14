import json
import time
import requests
import uuid
import sys
import os
from collections import defaultdict
from dotenv import load_dotenv

# Load env vars for API Key
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

# Add project root to path to import metrics_utils
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.evaluation.metrics_utils import (
    calculate_accuracy, 
    calculate_semantic_match_llm,
    calculate_semantic_recall_precision_llm,
    calculate_f1_score
)

API_URL = "http://localhost:8000/api/v1/chat"
DATASET_PATH = os.path.join(os.path.dirname(__file__), "test_dataset.json")
NVIDIA_API_KEY = os.getenv("NVIDIA_LLM_API_KEY")

def run_benchmark():
    print("Starting Comprehensive Benchmark (Spec 6.2 Metrics)...")
    
    # 1. Load Dataset
    if not os.path.exists(DATASET_PATH):
        print(f"Error: Dataset not found at {DATASET_PATH}")
        return

    with open(DATASET_PATH, 'r', encoding='utf-8') as f:
        cases = json.load(f)
    
    print(f"Loaded {len(cases)} test cases.")
    
    # Aggregators
    total_strict_acc = 0.0
    total_semantic_acc = 0.0
    total_recall = 0.0
    total_precision = 0.0
    total_f1 = 0.0
    total_latency = 0.0
    successful_cases = 0
    
    # Confusion Matrix Tracker (Expected -> [Predicted1, Predicted2...])
    confusion_data = defaultdict(list)
    
    print("-" * 100)
    print(f"{'Case ID':<10} | {'Diagnosis':<15} | {'Str.':<5} | {'Sem.':<5} | {'Rec':<5} | {'Pre':<5} | {'F1':<5} | {'Time'}")
    print("-" * 100)

    for case in cases:
        case_id = case['id']
        input_text = case['input_text']
        expected_diag = case['expected_diagnosis']
        
        # Prepare Request
        payload = {
            "session_id": f"bench_{uuid.uuid4().hex[:8]}",
            "patient_id": "benchmark_patient",
            "message": input_text
        }
        
        try:
            start_time = time.time()
            response = requests.post(API_URL, json=payload)
            latency = (time.time() - start_time) * 1000 # ms
            
            if response.status_code == 200:
                data = response.json()
                
                # Extract Predictions
                candidates = []
                predicted_top1 = ""
                
                if data.get('diagnosis_list'):
                    # Get top 3 candidates names
                    candidates = [d['disease_name'] for d in data['diagnosis_list'][:3]]
                    predicted_top1 = candidates[0]
                
                # 1. Accuracy Metrics
                strict_acc = calculate_accuracy(predicted_top1, expected_diag)
                
                # Semantic Accuracy (LLM Judge) - Top 1
                semantic_acc = strict_acc
                if strict_acc < 1.0 and NVIDIA_API_KEY:
                    print(f" [Eval] ", end="", flush=True)
                    semantic_acc = calculate_semantic_match_llm(predicted_top1, expected_diag, NVIDIA_API_KEY)
                
                # 2. Recall / Precision / F1 (Based on Candidates)
                recall, precision = calculate_semantic_recall_precision_llm(candidates, expected_diag, NVIDIA_API_KEY)
                f1 = calculate_f1_score(precision, recall)
                
                # Update Totals
                total_strict_acc += strict_acc
                total_semantic_acc += semantic_acc
                total_recall += recall
                total_precision += precision
                total_f1 += f1
                total_latency += latency
                successful_cases += 1
                
                # Confusion Data
                confusion_data[expected_diag].append(predicted_top1)
                
                print(f"{case_id:<10} | {predicted_top1[:15]:<15} | {strict_acc:<5.1f} | {semantic_acc:<5.1f} | {recall:<5.1f} | {precision:<5.1f} | {f1:<5.2f} | {latency:<4.0f}")
                
            else:
                print(f"{case_id:<10} | {'ERROR':<15} | 0.0   | 0.0   | 0.0   | 0.0   | 0.0   | {latency:<4.0f}")

        except Exception as e:
            print(f"Error processing {case_id}: {str(e)}")

    print("-" * 100)
    
    if successful_cases > 0:
        avg_strict = total_strict_acc / successful_cases
        avg_semantic = total_semantic_acc / successful_cases
        avg_recall = total_recall / successful_cases
        avg_precision = total_precision / successful_cases
        avg_f1 = total_f1 / successful_cases
        avg_lat = total_latency / successful_cases
        
        print(f"\n=== Benchmark Report (Spec 6.2) ===")
        print(f"Total Cases: {len(cases)} (Successful: {successful_cases})")
        print(f"[A. Accuracy]")
        print(f"  Top-1 Semantic Acc: {avg_semantic:.2%}")
        print(f"  Semantic Recall:    {avg_recall:.2%}")
        print(f"  Semantic Precision: {avg_precision:.2%}")
        print(f"  F1-Score:           {avg_f1:.2%}")
        print(f"[B. Efficiency]")
        print(f"  Avg Latency:        {avg_lat:.0f} ms")
        
        print(f"\n[A.5 Confusion Matrix Summary] (Expected -> Predicted Count)")
        for exp, preds in confusion_data.items():
            pred_counts = {}
            for p in preds:
                pred_counts[p] = pred_counts.get(p, 0) + 1
            print(f"  Expected '{exp}': {pred_counts}")
            
    else:
        print("No cases successfully processed.")

if __name__ == "__main__":
    run_benchmark()