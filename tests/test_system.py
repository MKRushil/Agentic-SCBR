#!/usr/bin/env python3
"""
中醫 CBR 診斷系統 - 完整測試腳本
測試整個系統的運行流程
"""

import sys
import time
import requests
import json
from pathlib import Path

# 顏色輸出
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'

def print_step(step, msg):
    print(f"\n{'='*60}")
    print(f"{Colors.BLUE}步驟 {step}: {msg}{Colors.RESET}")
    print('='*60)

def print_success(msg):
    print(f"{Colors.GREEN}✅ {msg}{Colors.RESET}")

def print_error(msg):
    print(f"{Colors.RED}❌ {msg}{Colors.RESET}")

def print_warning(msg):
    print(f"{Colors.YELLOW}⚠️  {msg}{Colors.RESET}")

# FastAPI 服務地址
BASE_URL = "http://localhost:8000"

# 測試案例數據
test_query = {
    "patient_info": {
        "age": 45,
        "gender": "女",
        "medical_history": "高血壓病史5年"
    },
    "chief_complaint": "頭痛眩暈",
    "symptoms": [
        "頭痛",
        "眩暈",
        "耳鳴",
        "失眠",
        "煩躁易怒",
        "口苦"
    ],
    "tongue": {
        "color": "紅",
        "coating": "黃"
    },
    "pulse": "弦數"
}

def test_1_health_check():
    """測試 1: 健康檢查"""
    print_step(1, "健康檢查")

    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print_success(f"API 服務運行中: {data}")
            return True
        else:
            print_error(f"健康檢查失敗: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print_error("無法連接到 API 服務")
        print_warning("請確保 FastAPI 服務正在運行:")
        print_warning("  python main.py")
        return False
    except Exception as e:
        print_error(f"健康檢查異常: {e}")
        return False

def test_2_weaviate_status():
    """測試 2: Weaviate 狀態"""
    print_step(2, "檢查 Weaviate 向量庫")

    try:
        response = requests.get(f"{BASE_URL}/system/status", timeout=5)
        if response.status_code == 200:
            data = response.json()
            weaviate_status = data.get("weaviate", {})

            if weaviate_status.get("connected"):
                print_success(f"Weaviate 已連接")
                print(f"  - 案例數量: {weaviate_status.get('case_count', 0)}")
                print(f"  - 集合名稱: {weaviate_status.get('collection')}")
                return True
            else:
                print_warning("Weaviate 未連接 (將使用傳統檢索)")
                return True  # 不阻止測試繼續
        else:
            print_error(f"獲取系統狀態失敗: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"檢查 Weaviate 狀態異常: {e}")
        return False

def test_3_diagnose():
    """測試 3: 診斷推理"""
    print_step(3, "執行診斷推理")

    print("\n測試查詢:")
    print(json.dumps(test_query, ensure_ascii=False, indent=2))

    try:
        response = requests.post(
            f"{BASE_URL}/diagnose",
            json=test_query,
            timeout=60
        )

        if response.status_code == 200:
            result = response.json()
            print_success("診斷成功!")

            # 顯示診斷結果
            print(f"\n{Colors.BLUE}診斷結果:{Colors.RESET}")
            print(f"  - 證型: {result.get('syndrome', 'N/A')}")
            print(f"  - 治法: {result.get('treatment_principle', 'N/A')}")
            print(f"  - 方劑: {result.get('formula', 'N/A')}")
            print(f"  - 藥物: {', '.join(result.get('herbs', []))}")

            # 相似案例
            similar_cases = result.get('similar_cases', [])
            print(f"\n  - 相似案例數: {len(similar_cases)}")
            for i, case in enumerate(similar_cases[:3], 1):
                print(f"    {i}. {case.get('case_id')} (相似度: {case.get('similarity_score', 0):.2%})")

            # 推理過程
            if 'reasoning' in result:
                print(f"\n{Colors.BLUE}推理依據:{Colors.RESET}")
                reasoning = result['reasoning'][:200] + "..." if len(result['reasoning']) > 200 else result['reasoning']
                print(f"  {reasoning}")

            return result
        else:
            print_error(f"診斷失敗: {response.status_code}")
            print(f"錯誤信息: {response.text}")
            return None

    except requests.exceptions.Timeout:
        print_error("請求超時 (60秒)")
        return None
    except Exception as e:
        print_error(f"診斷異常: {e}")
        return None

def test_4_review_and_retain():
    """測試 4: 專家審核與案例保留"""
    print_step(4, "專家審核與案例保留")

    # 先執行一次診斷獲取 query_id
    response = requests.post(f"{BASE_URL}/diagnose", json=test_query, timeout=60)
    if response.status_code != 200:
        print_error("無法獲取診斷結果進行審核測試")
        return False

    result = response.json()
    query_id = result.get('query_id')

    if not query_id:
        print_warning("診斷結果沒有 query_id,跳過審核測試")
        return True

    # 模擬專家審核
    review_data = {
        "query_id": query_id,
        "expert_feedback": {
            "approved": True,
            "syndrome": result.get('syndrome'),
            "treatment_principle": result.get('treatment_principle'),
            "formula": result.get('formula'),
            "herbs": result.get('herbs'),
            "modifications": "無需修改",
            "comments": "診斷準確,符合臨床實際"
        },
        "retain_case": True
    }

    try:
        response = requests.post(
            f"{BASE_URL}/review",
            json=review_data,
            timeout=10
        )

        if response.status_code == 200:
            print_success("專家審核成功")
            review_result = response.json()
            if review_result.get('case_retained'):
                print_success(f"案例已保留到案例庫")
                print(f"  案例ID: {review_result.get('case_id')}")
            return True
        else:
            print_error(f"審核失敗: {response.status_code}")
            return False

    except Exception as e:
        print_error(f"審核異常: {e}")
        return False

def test_5_case_search():
    """測試 5: 案例檢索"""
    print_step(5, "案例檢索功能")

    search_criteria = {
        "symptoms": ["頭痛", "眩暈"],
        "syndrome": "肝陽上亢",
        "top_k": 3
    }

    try:
        response = requests.post(
            f"{BASE_URL}/cases/search",
            json=search_criteria,
            timeout=10
        )

        if response.status_code == 200:
            cases = response.json()
            print_success(f"檢索到 {len(cases)} 個案例")
            for i, case in enumerate(cases, 1):
                print(f"  {i}. {case.get('case_id')} - {case.get('syndrome')}")
            return True
        else:
            print_warning(f"案例檢索失敗: {response.status_code}")
            return True  # 不阻止測試

    except Exception as e:
        print_error(f"檢索異常: {e}")
        return False

def test_6_statistics():
    """測試 6: 系統統計"""
    print_step(6, "系統統計信息")

    try:
        response = requests.get(f"{BASE_URL}/stats", timeout=5)

        if response.status_code == 200:
            stats = response.json()
            print_success("統計信息獲取成功")
            print(f"\n{Colors.BLUE}系統統計:{Colors.RESET}")
            print(f"  - 總診斷次數: {stats.get('total_queries', 0)}")
            print(f"  - 案例庫大小: {stats.get('case_library_size', 0)}")
            print(f"  - 向量庫案例數: {stats.get('vector_store_size', 0)}")
            print(f"  - 平均響應時間: {stats.get('avg_response_time', 0):.2f}秒")
            return True
        else:
            print_warning(f"獲取統計失敗: {response.status_code}")
            return True

    except Exception as e:
        print_error(f"統計異常: {e}")
        return False

def test_7_performance():
    """測試 7: 性能測試"""
    print_step(7, "性能測試 (5次診斷)")

    times = []
    for i in range(5):
        print(f"\n執行第 {i+1} 次診斷...", end=" ")
        start = time.time()

        try:
            response = requests.post(
                f"{BASE_URL}/diagnose",
                json=test_query,
                timeout=60
            )
            elapsed = time.time() - start

            if response.status_code == 200:
                times.append(elapsed)
                print(f"{Colors.GREEN}✓{Colors.RESET} ({elapsed:.2f}秒)")
            else:
                print(f"{Colors.RED}✗{Colors.RESET}")
        except Exception as e:
            print(f"{Colors.RED}✗ {e}{Colors.RESET}")

    if times:
        avg_time = sum(times) / len(times)
        min_time = min(times)
        max_time = max(times)

        print(f"\n{Colors.BLUE}性能統計:{Colors.RESET}")
        print(f"  - 平均響應時間: {avg_time:.2f}秒")
        print(f"  - 最快響應: {min_time:.2f}秒")
        print(f"  - 最慢響應: {max_time:.2f}秒")
        print_success(f"性能測試完成 ({len(times)}/5 成功)")
        return True
    else:
        print_error("所有請求都失敗了")
        return False

def main():
    """主測試流程"""
    print(f"\n{Colors.BLUE}{'='*60}")
    print("中醫 CBR 診斷系統 - 完整測試")
    print(f"{'='*60}{Colors.RESET}")

    results = {}

    # 執行所有測試
    tests = [
        ("健康檢查", test_1_health_check),
        ("Weaviate 狀態", test_2_weaviate_status),
        ("診斷推理", test_3_diagnose),
        ("專家審核", test_4_review_and_retain),
        ("案例檢索", test_5_case_search),
        ("系統統計", test_6_statistics),
        ("性能測試", test_7_performance),
    ]

    for name, test_func in tests:
        try:
            result = test_func()
            results[name] = result

            # 如果關鍵測試失敗,停止後續測試
            if name in ["健康檢查"] and not result:
                print_error("\n關鍵測試失敗,終止後續測試")
                break

        except KeyboardInterrupt:
            print("\n\n測試被用戶中斷")
            break
        except Exception as e:
            print_error(f"測試異常: {e}")
            results[name] = False

    # 測試總結
    print(f"\n{Colors.BLUE}{'='*60}")
    print("測試總結")
    print(f"{'='*60}{Colors.RESET}")

    passed = sum(1 for r in results.values() if r)
    total = len(results)

    for name, result in results.items():
        status = f"{Colors.GREEN}✅ 通過{Colors.RESET}" if result else f"{Colors.RED}❌ 失敗{Colors.RESET}"
        print(f"  {name}: {status}")

    print(f"\n總計: {passed}/{total} 測試通過")

    if passed == total:
        print_success("\n🎉 所有測試通過!")
        return 0
    else:
        print_warning(f"\n⚠️  {total - passed} 個測試失敗")
        return 1

if __name__ == "__main__":
    sys.exit(main())
