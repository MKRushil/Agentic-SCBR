import json
import time
import requests
import uuid
import sys
import os
import csv  # [修正 3] 補上 missing import
import asyncio
import numpy as np
from datetime import datetime # [修正 3] 補上 missing import
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

settings = get_settings()

async def get_embedding(text):
    """
    獲取真實的 NVIDIA Embedding 向量 (1024 維)。
    """
    if not text: return None
    try:
        url = "https://integrate.api.nvidia.com/v1/embeddings"
        headers = {
            "Authorization": f"Bearer {settings.NVIDIA_EMBEDDING_API_KEY}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        payload = {
            "model": settings.EMBEDDING_MODEL_NAME,
            "input": [text],
            "input_type": "query",
            "encoding_format": "float"
        }
        # 使用 requests 同步調用 (在 async 包裝下)
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        data = response.json()
        return data['data'][0]['embedding']
    except Exception as e:
        print(f"Error getting embedding for '{str(text)[:10]}...': {e}")
        return None

def run_benchmark():
    print("Starting SCBR Multi-Turn Benchmark (vFinal - Strict Mode)...")
    
    if not os.path.exists(DATASET_PATH):
        print(f"Error: Dataset not found at {DATASET_PATH}")
        return

    with open(DATASET_PATH, 'r', encoding='utf-8') as f:
        cases = json.load(f)
    
    evaluator = SCBREvaluator()
    
    for case in cases:
        case_id = case['id']
        category = case.get('category', 'Uncategorized')
        session_id = f"bench_{uuid.uuid4().hex[:8]}"
        print(f"\n--- Processing Case: {case_id} ({category}) ---")
        
        # 獲取 GT 向量
        gt_text = case.get('expected_diagnosis', "")
        gt_vector = asyncio.run(get_embedding(gt_text))
        
        # 獲取 GT 屬性
        gt_attributes = case.get('expected_attributes', {})

        turns = case.get('turns', [])
        
        for turn_idx, turn in enumerate(turns):
            turn_id = turn_idx + 1
            user_input = turn.get('input', "")
            
            # Ground Truths
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
                    
                    # 2. 提取結構化屬性 (Directly from LLM)
                    standardized = data.get('standardized_features', {})
                    pred_attributes = standardized.get('pred_attributes', {})
                    
                    # [Fallback] 若 LLM 未輸出 (例如舊版)，保留空字典或進行簡單補救 (這裡選擇信任 LLM)
                    if not pred_attributes:
                        # Optional: Log warning
                        # print(f"Warning: pred_attributes missing for {session_id}")
                        pass

                    # [修正 2] 提取風險等級 (Risk Level) - 為了 Metric 10 Funnel Adherence
                    pred_risk = data.get('risk_level', 'GREEN')

                    # 3. 提取模糊項計數
                    amb_count = len(standardized.get('ambiguous_terms', []))
                    
                    # 4. 獲取預測向量
                    pred_vector = asyncio.run(get_embedding(pred_diag)) if pred_diag else None

                    # Log 到 Evaluator
                    turn_data = {
                        "case_id": case_id,
                        "category": category,
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
                        "pred_risk_level": pred_risk, # [修正 2] 傳入 Evaluator
                        "ambiguous_terms_count": amb_count,
                        
                        "is_rejected_action": "CASE_REJECTED" in data.get('evidence_trace', "")
                    }
                    evaluator.log_turn(turn_data)
                    
                    print(f"[{pred_type}] {pred_diag} (Conf: {pred_conf:.2f})")
                    
                else:
                    print(f"Error {resp.status_code}")

            except Exception as e:
                print(f"Exception: {str(e)}")
                
    # Final Report
    print("\n" + "="*60)
    print("SCBR vFinal Evaluation Report (10 Metrics)")
    print("="*60)
    
    summary_metrics = evaluator.get_summary_report()

    # 輸出設定
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = os.path.join(os.path.dirname(__file__), "reports")
    os.makedirs(output_dir, exist_ok=True)

    # 1. 輸出 JSON
    raw_file_path = os.path.join(output_dir, f"benchmark_raw_{timestamp}.json")
    report_data = {
        "meta": {"timestamp": timestamp, "total_cases": len(cases)},
        "metrics": summary_metrics,
        "logs": evaluator.logs
    }
    with open(raw_file_path, 'w', encoding='utf-8') as f:
        json.dump(report_data, f, ensure_ascii=False, indent=2)
    print(f"\n[Saved] Raw Data: {raw_file_path}")

    # 2. 輸出 CSV
    csv_file_path = os.path.join(output_dir, f"benchmark_metrics_{timestamp}.csv")
    with open(csv_file_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["Metric Type", "Metric Name", "Value"])
        for key, val in summary_metrics.items():
            if key == "Category_Breakdown": continue
            m_type = "Accuracy" if key.startswith("A") else ("Efficiency" if key.startswith("B") else "Trajectory")
            writer.writerow([m_type, key, f"{val:.4f}"])
        
        writer.writerow([])
        writer.writerow(["Category", "Hybrid_Accuracy_Score"])
        cat_breakdown = summary_metrics.get("Category_Breakdown", {})
        for cat, score in cat_breakdown.items():
            writer.writerow([cat, f"{score:.4f}"])
    print(f"[Saved] Metrics CSV: {csv_file_path}")

    # 3. 輸出 Markdown
    md_file_path = os.path.join(output_dir, f"benchmark_report_{timestamp}.md")
    with open(md_file_path, 'w', encoding='utf-8') as f:
        f.write(f"# SCBR System Evaluation Report\n")
        f.write(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        f.write("## 1. Overall Performance\n")
        f.write("| Metric | Value |\n| :--- | :--- |\n")
        for key, val in summary_metrics.items():
            if key == "Category_Breakdown": continue
            f.write(f"| {key} | **{val:.4f}** |\n")
            
        f.write("\n## 2. Category Breakdown\n")
        f.write("| Category | Hybrid Accuracy |\n| :--- | :--- |\n")
        for cat, score in cat_breakdown.items():
            f.write(f"| {cat} | {score:.4f} |\n")

    print(f"[Saved] Report MD: {md_file_path}")
    print("="*60)

if __name__ == "__main__":
    run_benchmark()