import json
import time
import requests
import uuid
import sys
import os
import numpy as np
from dotenv import load_dotenv

# Load env
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

# Import NvidiaClient and Settings
from app.services.nvidia_client import NvidiaClient
from app.core.config import get_settings

from app.evaluation.scbr_evaluator import SCBREvaluator

API_URL = "http://localhost:8000/api/v1/chat"
DATASET_PATH = os.path.join(os.path.dirname(__file__), "test_dataset.json")

# Initialize NvidiaClient for embedding
settings = get_settings()
nvidia_client = NvidiaClient()

async def get_embedding(text):
    """
    獲取真實的 NVIDIA Embedding 向量 (1024 維)。
    """
    if not text: return None
    try:
        # Assuming get_embedding is an async method in NvidiaClient
        # For synchronous context, run asyncio.run(nvidia_client.get_embedding(text))
        # Or, modify NvidiaClient to have a sync get_embedding_sync if needed
        # For now, let's use requests directly to avoid async in sync context
        url = "https://integrate.api.nvidia.com/v1/embeddings"
        headers = {
            "Authorization": f"Bearer {settings.NVIDIA_EMBEDDING_API_KEY}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        payload = {
            "model": settings.EMBEDDING_MODEL_NAME,
            "input": text
        }
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()
        return data['data'][0]['embedding']
    except Exception as e:
        print(f"Error getting embedding for '{text[:50]}...': {e}")
        return None

def run_benchmark():
    print("Starting SCBR Multi-Turn Benchmark (vFinal)...")
    
    if not os.path.exists(DATASET_PATH):
        print(f"Error: Dataset not found at {DATASET_PATH}")
        return

    with open(DATASET_PATH, 'r', encoding='utf-8') as f:
        cases = json.load(f)
    
    evaluator = SCBREvaluator()
    
    for case in cases:
        case_id = case['id']
        session_id = f"bench_{uuid.uuid4().hex[:8]}"
        print(f"\n--- Processing Case: {case_id} ---")
        
        # 獲取 GT 向量 (只做一次，為了 Metric 1)
        gt_text = case.get('expected_diagnosis', "")
        # Run the async get_embedding in a synchronous way for benchmark
        import asyncio
        gt_vector = asyncio.run(get_embedding(gt_text)) # Await the embedding
        
        # 獲取 GT 屬性
        gt_attributes = case.get('expected_attributes', {})

        turns = case.get('turns', [])
        
        for turn_idx, turn in enumerate(turns):
            turn_id = turn_idx + 1 # 從 1 開始
            user_input = turn.get('input', "")
            
            # Ground Truths (for each turn, or from case level)
            # Make sure gt_diagnosis is defined for each turn or fallback to case level
            gt_diagnosis = turn.get('expected_diagnosis', case.get('expected_diagnosis'))
            is_emergency = turn.get('is_emergency', case.get('is_emergency', False))
            
            print(f"  Turn {turn_id}: Input='{user_input[:30]}...' -> ", end="", flush=True)
            
            payload = {
                "session_id": session_id,
                "patient_id": "benchmark_patient",
                "message": user_input
            }
            
            try:
                resp = requests.post(API_URL, json=payload)
                
                if resp.status_code == 200:
                    data = resp.json()
                    
                    # 1. 提取預測結果
                    pred_type = data.get('response_type', 'FALLBACK')
                    pred_diag = ""
                    pred_conf = 0.0
                    
                    if data.get('diagnosis_list'):
                        top1 = data['diagnosis_list'][0]
                        pred_diag = top1.get('disease_name', "")
                        pred_conf = top1.get('confidence', 0.0)
                    
                    # 2. 提取結構化屬性 (Crucial for Logic Checks)
                    pred_attributes = {}
                    # 從 Translator 的八綱分數推斷屬性 (standardized_features)
                    if data.get('standardized_features'):
                        eight_principles = data['standardized_features'].get('eight_principles_score', {})
                        han = eight_principles.get('han', 0)
                        re = eight_principles.get('re', 0)
                        xu = eight_principles.get('xu', 0)
                        shi = eight_principles.get('shi', 0)
                        
                        pred_attributes['nature'] = 'cold' if han > re else ('hot' if re > han else 'neutral')
                        pred_attributes['deficiency'] = 'deficiency' if xu > shi else ('excess' if shi > xu else 'neutral')
                    
                    # 3. 提取模糊項計數
                    amb_count = len(data.get('standardized_features', {}).get('ambiguous_terms', []))
                    
                    # 4. 獲取預測向量 (Metric 1)
                    pred_vector = asyncio.run(get_embedding(pred_diag)) if pred_diag else None

                    # Log 到 Evaluator
                    turn_data = {
                        "case_id": case_id,
                        "turn_id": turn_id,
                        "input_text": user_input,
                        "gt_diagnosis": gt_diagnosis,
                        "gt_attributes": gt_attributes,
                        "gt_vector": gt_vector,
                        "is_emergency_gt": is_emergency,
                        
                        "pred_response_type": pred_type,
                        "pred_diagnosis": pred_diag,
                        "pred_confidence": pred_conf,
                        "pred_attributes": pred_attributes, 
                        "pred_vector": pred_vector,
                        "ambiguous_terms_count": amb_count,
                        
                        "is_rejected_action": "CASE_REJECTED" in data.get('evidence_trace', "") # 從 trace 判斷
                    }
                    evaluator.log_turn(turn_data)
                    
                    print(f"  Turn {turn_id}: [{pred_type}] {pred_diag} (Conf: {pred_conf:.2f})")
                    
                else:
                    print(f"  Turn {turn_id}: Error {resp.status_code}")

            except Exception as e:
                print(f"  Exception: {str(e)}")
                
    # Final Report
    print("\n" + "="*60)
    print("SCBR vFinal Evaluation Report (10 Metrics)")
    print("="*60)
    
    results = evaluator.get_summary_report()
    for metric, value in results.items():
        print(f"{metric:<30}: {value:.4f}")
    print("="*60)

if __name__ == "__main__":
    run_benchmark()
