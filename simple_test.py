#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
簡化的 LLM API 測試程式
專門測試已知可用的 /chat/completions 端點
"""

import requests
import json
import time


def simple_test():
    """簡單的 API 測試"""
    base_url = "https://83223c7508ae.ngrok-free.app"
    url = f"{base_url}/chat/completions"
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer sk-local-123",
        "ngrok-skip-browser-warning": "true"
    }
    
    payload = {
        "model": "gpt-oss-120b",
        "messages": [
            {"role": "user", "content": "請用10個字介紹你自己"}
        ],
        "temperature": 0.7,
        "stream": False
    }
    
    print("🚀 開始簡單 API 測試")
    print("=" * 50)
    print(f"目標 URL: {url}")
    print(f"請求標頭: {json.dumps(headers, ensure_ascii=False, indent=2)}")
    print(f"請求內容: {json.dumps(payload, ensure_ascii=False, indent=2)}")
    print()
    
    try:
        start_time = time.time()
        
        # ngrok 預熱機制：先發送 GET 請求來喚醒服務
        print("🔄 ngrok 預熱中...")
        try:
            warmup_response = requests.get(
                base_url,
                headers={"ngrok-skip-browser-warning": "true"},
                timeout=5
            )
            print(f"   預熱 GET 請求狀態碼: {warmup_response.status_code}")
            time.sleep(0.5)  # 稍微等待一下讓連線穩定
        except Exception as e:
            print(f"   預熱請求失敗 (可忽略): {e}")
        
        print("📤 發送主要 POST 請求...")
        response = requests.post(
            url,
            headers=headers,
            json=payload,
            timeout=30
        )
        
        end_time = time.time()
        
        print(f"⏱️  請求耗時: {end_time - start_time:.2f} 秒")
        print(f"📊 回應狀態碼: {response.status_code}")
        print(f"📋 回應標頭: {dict(response.headers)}")
        print()
        
        if response.status_code == 200:
            print("✅ 請求成功！")
            try:
                result = response.json()
                print("🤖 AI 回應:")
                if "choices" in result and len(result["choices"]) > 0:
                    content = result["choices"][0]["message"]["content"]
                    print(f"   {content}")
                else:
                    print(f"   完整回應: {json.dumps(result, ensure_ascii=False, indent=2)}")
            except json.JSONDecodeError:
                print(f"   原始回應: {response.text}")
        else:
            print(f"❌ 請求失敗 (狀態碼: {response.status_code})")
            print(f"錯誤內容: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ 網路請求錯誤: {e}")
    except Exception as e:
        print(f"❌ 其他錯誤: {e}")


if __name__ == "__main__":
    simple_test()
