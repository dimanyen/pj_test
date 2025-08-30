#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LLM API 呼叫測試程式
參考 curl 指令建立對應的 Python 實作
"""

import requests
import json
import time
from typing import Dict, List, Optional


class LLMAPI:
    """LLM API 呼叫類別"""
    
    def __init__(self, base_url: str, api_key: str):
        """
        初始化 LLM API 客戶端
        
        Args:
            base_url: API 基礎 URL
            api_key: API 金鑰
        """
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
            "ngrok-skip-browser-warning": "true"
        }
    
    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: str = "gpt-oss-120b",
        temperature: float = 0.7,
        stream: bool = False
    ) -> Dict:
        """
        發送聊天完成請求
        
        Args:
            messages: 訊息列表，格式為 [{"role": "user", "content": "..."}]
            model: 使用的模型名稱
            temperature: 溫度參數，控制回應的隨機性
            stream: 是否使用串流模式
            
        Returns:
            API 回應的字典
        """
        url = f"{self.base_url}/chat/completions"
        
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "stream": stream
        }
        
        try:
            print(f"發送請求到: {url}")
            print(f"請求標頭: {json.dumps(dict(self.headers), ensure_ascii=False, indent=2)}")
            print(f"請求內容: {json.dumps(payload, ensure_ascii=False, indent=2)}")
            
            # ngrok 預熱機制：先發送 GET 請求來喚醒服務
            print("🔄 ngrok 預熱中...")
            try:
                warmup_response = requests.get(
                    self.base_url,
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
                headers=self.headers,
                json=payload,
                timeout=30
            )
            
            print(f"回應狀態碼: {response.status_code}")
            print(f"回應標頭: {dict(response.headers)}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"回應內容: {json.dumps(result, ensure_ascii=False, indent=2)}")
                return result
            else:
                print(f"錯誤回應狀態碼: {response.status_code}")
                print(f"錯誤回應內容: {response.text}")
                print(f"錯誤回應標頭: {dict(response.headers)}")
                return {"error": response.status_code, "message": response.text}
                
        except requests.exceptions.RequestException as e:
            print(f"請求錯誤: {e}")
            return {"error": "request_error", "message": str(e)}
        except json.JSONDecodeError as e:
            print(f"JSON 解析錯誤: {e}")
            print(f"原始回應: {response.text[:500]}...")
            return {"error": "json_error", "message": str(e)}


def main():
    """主程式"""
    # API 設定
    BASE_URL = "https://llm.cubeapp945566.work"
    API_KEY = "sk-local-123"
    
    # 建立 API 客戶端
    api = LLMAPI(BASE_URL, API_KEY)
    
    # 測試訊息
    test_messages = [
        {"role": "user", "content": "請用10個字介紹你自己"}
    ]
    
    print("=" * 50)
    print("LLM API 呼叫測試")
    print("=" * 50)
    
    # 發送請求
    start_time = time.time()
    result = api.chat_completion(
        messages=test_messages,
        model="gpt-oss-120b",
        temperature=0.7,
        stream=False
    )
    end_time = time.time()
    
    print("\n" + "=" * 50)
    print("測試結果摘要")
    print("=" * 50)
    print(f"請求耗時: {end_time - start_time:.2f} 秒")
    
    if "error" not in result:
        print("✅ API 呼叫成功")
        if "choices" in result and len(result["choices"]) > 0:
            content = result["choices"][0]["message"]["content"]
            print(f"AI 回應: {content}")
    else:
        print(f"❌ API 呼叫失敗: {result.get('message', '未知錯誤')}")


if __name__ == "__main__":
    main()
