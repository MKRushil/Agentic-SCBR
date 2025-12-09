import requests
import json
import time
from typing import Dict, Any

# API 配置
API_BASE_URL = "http://localhost:8000"

def print_header(text: str):
    """打印標題"""
    print("\n" + "="*60)
    print(text)
    print("="*60)

def print_step(step: str):
    """打印步驟"""
    print(f"\n{step}")
    print("-"*60)

def test_health_check() -> bool:
    """測試健康檢查"""
    print_step("步驟 1: 健康檢查")
    try:
        response = requests.get(f"{API_BASE_URL}/health")
        if response.status_code == 200:
            result = response.json()
            print(f"✅ API 服務運行中: {result}")
            return True
        else:
            print(f"❌ 健康檢查失敗: {response.status_code}")
            print(f"響應內容: {response.text}")
            return False
    except Exception as e:
        print(f"❌ 健康檢查異常: {e}")
        print(f"\n請確認 FastAPI 是否正在運行: python main.py")
        return False

def test_diagnosis() -> bool:
    """測試診斷功能"""
    print_step("步驟 2: 執行診斷推理")

    query = {
        "chief_complaint": "頭痛眩暈",
        "symptoms": ["頭痛", "眩暈", "耳鳴", "失眠"],
        "tongue": {"color": "紅", "coating": "黃"},
        "pulse": "弦數"
    }

    print(f"\n測試查詢:")
    print(json.dumps(query, ensure_ascii=False, indent=2))

    try:
        response = requests.post(
            f"{API_BASE_URL}/diagnose",
            json=query,
            headers={"Content-Type": "application/json"}
        )

        if response.status_code == 200:
            result = response.json()
            print(f"\n✅ 診斷成功!")
            print(f"\n診斷結果:")
            print(f"  - 證型: {result.get('syndrome', 'N/A')}")
            print(f"  - 治法: {result.get('treatment_principle', 'N/A')}")
            print(f"  - 方劑: {result.get('formula', 'N/A')}")
            print(f"  - 藥物: {', '.join(result.get('herbs', []))}")
            print(f"  - 相似案例數: {len(result.get('similar_cases', []))}")
            return True
        else:
            print(f"❌ 診斷失敗: {response.status_code}")
            print(f"響應: {response.text}")
            return False
    except Exception as e:
        print(f"❌ 診斷異常: {e}")
        return False

def main():
    """主測試流程"""
    print_header("中醫 CBR 診斷系統 - 快速測試")

    results = {
        "健康檢查": False,
        "診斷推理": False,
    }

    # 1. 健康檢查
    results["健康檢查"] = test_health_check()

    if not results["健康檢查"]:
        print("\n❌ 服務未啟動,終止測試")
        print("\n請先啟動服務: python main.py")
        return

    # 2. 診斷測試
    results["診斷推理"] = test_diagnosis()

    # 總結
    print_header("測試總結")
    for name, passed in results.items():
        status = "✅ 通過" if passed else "❌ 失敗"
        print(f"  {name}: {status}")

    total = len(results)
    passed = sum(1 for v in results.values() if v)
    print(f"\n總計: {passed}/{total} 測試通過")

    if passed == total:
        print("\n🎉 所有測試通過!")

if __name__ == "__main__":
    main()
