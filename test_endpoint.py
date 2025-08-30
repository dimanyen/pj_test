#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API 端點診斷測試程式
用於檢查 API 服務的狀態和可用性
"""

import requests
import time
import json


def test_endpoint_health(base_url: str):
    """測試端點健康狀態"""
    print(f"測試端點: {base_url}")
    print("=" * 50)
    
    # 測試 1: 基本連線
    # print("1. 測試基本連線...")
    # try:
    #     response = requests.get(base_url, timeout=10)
    #     print(f"   狀態碼: {response.status_code}")
    #     print(f"   回應類型: {response.headers.get('Content-Type', 'unknown')}")
    #     if response.status_code == 200:
    #         print("   ✅ 基本連線成功")
    #     else:
    #         print(f"   ⚠️  連線成功但狀態碼異常: {response.status_code}")
    # except Exception as e:
    #     print(f"   ❌ 連線失敗: {e}")
    
    # print()
    
    # # 測試 2: 檢查根路徑
    # print("2. 測試根路徑...")
    # try:
    #     response = requests.get(f"{base_url}/", timeout=10)
    #     print(f"   狀態碼: {response.status_code}")
    #     print(f"   回應類型: {response.headers.get('Content-Type', 'unknown')}")
    #     if "ngrok" in response.text.lower():
    #         print("   ℹ️  收到 ngrok 頁面")
    #     else:
    #         print("   ✅ 收到正常回應")
    # except Exception as e:
    #     print(f"   ❌ 測試失敗: {e}")
    
    # print()
    
    # # 測試 3: 檢查 API 路徑 (GET)
    # print("3. 測試 API 路徑 (GET)...")
    # api_paths = [
    #     "/chat/completions",
    #     "/v1/chat/completions",
    #     "/api/chat/completions",
    #     "/chat",
    #     "/health",
    #     "/status"
    # ]
    
    # for path in api_paths:
    #     try:
    #         response = requests.get(f"{base_url}{path}", timeout=10)
    #         print(f"   {path}: {response.status_code}")
    #         if response.status_code != 404:
    #             print(f"      ⚠️  發現可能的 API 端點: {path}")
    #     except Exception as e:
    #         print(f"   {path}: 連線失敗")
    
    # print()
    
    # # 測試 4: 檢查 ngrok 狀態
    # print("4. 檢查 ngrok 狀態...")
    # try:
    #     response = requests.get(f"{base_url}/status", timeout=10)
    #     if response.status_code == 200:
    #         print("   ✅ ngrok 狀態端點可達")
    #         print(f"   狀態內容: {response.text[:200]}...")
    #     else:
    #         print(f"   ⚠️  ngrok 狀態端點回應: {response.status_code}")
    # except Exception as e:
    #     print(f"   ❌ 無法檢查 ngrok 狀態: {e}")
    
    # print()
    
    # 測試 5: POST 請求測試
    print("5. 測試 POST 請求...")
    test_payloads = [
        {
            "name": "基本聊天請求",
            "path": "/chat/completions",
            "data": {
                "model": "gpt-oss-120b",
                "messages": [
                    {"role": "user", "content": "Hello"}
                ],
                "temperature": 0.7,
                "stream": False
            }
        },
        {
            "name": "v1 版本路徑",
            "path": "/v1/chat/completions",
            "data": {
                "model": "gpt-oss-120b",
                "messages": [
                    {"role": "user", "content": "Hello"}
                ],
                "temperature": 0.7,
                "stream": False
            }
        },
        {
            "name": "API 路徑",
            "path": "/api/chat/completions",
            "data": {
                "model": "gpt-oss-120b",
                "messages": [
                    {"role": "user", "content": "Hello"}
                ],
                "temperature": 0.7,
                "stream": False
            }
        },
        {
            "name": "簡化路徑",
            "path": "/chat",
            "data": {
                "model": "gpt-oss-120b",
                "messages": [
                    {"role": "user", "content": "Hello"}
                ],
                "temperature": 0.7,
                "stream": False
            }
        }
    ]
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer sk-local-123",
        "ngrok-skip-browser-warning": "true"
    }
    
    for test in test_payloads:
        print(f"   測試: {test['name']}")
        print(f"   路徑: {test['path']}")
        try:
            response = requests.post(
                f"{base_url}{test['path']}",
                headers=headers,
                json=test['data'],
                timeout=15
            )
            print(f"   狀態碼: {response.status_code}")
            print(f"   回應類型: {response.headers.get('Content-Type', 'unknown')}")
            
            if response.status_code == 200:
                print("      ✅ POST 請求成功！")
                try:
                    result = response.json()
                    print(f"      API 回應: {json.dumps(result, ensure_ascii=False, indent=6)}")
                except:
                    print(f"      回應內容: {response.text[:200]}...")
            elif response.status_code == 404:
                print("      ❌ 端點不存在")
            elif response.status_code == 405:
                print("      ⚠️  方法不允許 (可能需要 POST)")
            elif response.status_code == 401:
                print("      🔐 認證失敗")
            elif response.status_code == 400:
                print("      ⚠️  請求格式錯誤")
                print(f"      錯誤詳情: {response.text[:200]}...")
            else:
                print(f"      ⚠️  其他狀態碼: {response.status_code}")
                print(f"      回應內容: {response.text[:200]}...")
                
        except Exception as e:
            print(f"      ❌ 請求失敗: {e}")
        
        print()


def main():
    """主程式"""
    base_url = "https://llm.cubeapp945566.work"
    
    print("🔍 API 端點診斷工具 (含 POST 測試)")
    print("=" * 50)
    
    test_endpoint_health(base_url)
    
    print("\n" + "=" * 50)
    print("💡 建議解決方案:")
    print("1. 檢查 ngrok 服務是否正在運行")
    print("2. 重新啟動 ngrok 服務")
    print("3. 確認正確的 API 端點路徑")
    print("4. 檢查防火牆和網路設定")
    print("5. 確認 LLM 服務的 API 路徑設定")
    print("=" * 50)


if __name__ == "__main__":
    main()
