#!/usr/bin/env python3
"""快速測試 - 只測試核心功能"""

import requests
import json

BASE_URL = "http://localhost:8000"

# 測試數據
query = {
    "chief_complaint": "頭痛眩暈",
    "symptoms": ["頭痛", "眩暈", "耳鳴", "失眠"],
    "tongue": {"color": "紅", "coating": "黃"},
    "pulse": "弦數"
}

print("\n1. 測試健康檢查...")
try:
    r = requests.get(f"{BASE_URL}/health", timeout=5)
    print(f"✅ API 運行中: {r.json()}")
except:
    print("❌ API 服務未運行")
    exit(1)

print("\n2. 測試診斷...")
try:
    r = requests.post(f"{BASE_URL}/diagnose", json=query, timeout=60)
    if r.status_code == 200:
        result = r.json()
        print(f"✅ 診斷成功")
        print(f"   證型: {result.get('syndrome')}")
        print(f"   治法: {result.get('treatment_principle')}")
        print(f"   方劑: {result.get('formula')}")
    else:
        print(f"❌ 診斷失敗: {r.status_code}")
except Exception as e:
    print(f"❌ 錯誤: {e}")

print("\n✅ 快速測試完成!")
