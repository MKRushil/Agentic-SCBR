"""
檢查 FastAPI 服務是否正在運行
"""

import requests
import sys

def check_service():
    """檢查服務狀態"""
    print("檢查 FastAPI 服務...")
    print("="*60)

    try:
        # 嘗試連接
        response = requests.get("http://localhost:8000/health", timeout=5)

        if response.status_code == 200:
            print("✅ 服務正在運行!")
            print(f"響應: {response.json()}")
            return True
        else:
            print(f"❌ 服務響應異常: {response.status_code}")
            return False

    except requests.exceptions.ConnectionError:
        print("❌ 無法連接到服務")
        print("\n請確認:")
        print("1. 是否已啟動 FastAPI: python main.py")
        print("2. 服務是否運行在 http://localhost:8000")
        return False

    except requests.exceptions.Timeout:
        print("❌ 連接超時")
        return False

    except Exception as e:
        print(f"❌ 錯誤: {e}")
        return False

if __name__ == "__main__":
    result = check_service()
    sys.exit(0 if result else 1)