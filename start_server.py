#!/usr/bin/env python3
"""
知識庫問答系統啟動腳本
自動檢查並建立必要的索引，然後啟動 Flask 伺服器
"""

import os
import sys
import subprocess
from pathlib import Path

def check_dependencies():
    """檢查依賴套件"""
    try:
        import flask
        print("✓ Flask 已安裝")
    except ImportError:
        print("✗ Flask 未安裝，正在安裝...")
        subprocess.run([sys.executable, "-m", "pip", "install", "flask>=3.0.0"], check=True)
        print("✓ Flask 安裝完成")
    
    try:
        import flask_cors
        print("✓ Flask-CORS 已安裝")
    except ImportError:
        print("✗ Flask-CORS 未安裝，正在安裝...")
        subprocess.run([sys.executable, "-m", "pip", "install", "flask-cors>=4.0.0"], check=True)
        print("✓ Flask-CORS 安裝完成")

def check_knowledge_base():
    """檢查知識庫索引是否存在"""
    index_file = Path("kb.index")
    store_file = Path("kb_store.jsonl")
    
    if index_file.exists() and store_file.exists():
        print("✓ 知識庫索引已存在")
        return True
    else:
        print("✗ 知識庫索引不存在，正在建立...")
        
        # 檢查知識文件資料夾
        docs_folder = Path("knowledge_docs")
        if not docs_folder.exists():
            print("✗ 知識文件資料夾 'knowledge_docs' 不存在")
            return False
        
        # 建立知識庫索引
        try:
            result = subprocess.run([
                sys.executable, "kb_rag.py", "build", "--folder", "knowledge_docs"
            ], capture_output=True, text=True, check=True)
            print("✓ 知識庫索引建立成功")
            return True
        except subprocess.CalledProcessError as e:
            print(f"✗ 知識庫索引建立失敗: {e}")
            print(f"錯誤輸出: {e.stderr}")
            return False

def main():
    print("=== 知識庫問答系統啟動檢查 ===\n")
    
    # 檢查依賴套件
    try:
        check_dependencies()
    except Exception as e:
        print(f"✗ 依賴套件檢查失敗: {e}")
        return 1
    
    # 檢查知識庫
    if not check_knowledge_base():
        print("\n請確保:")
        print("1. knowledge_docs 資料夾存在且包含 .md 或 .txt 檔案")
        print("2. 環境變數設定正確 (LITELLM_BASE, LITELLM_API_KEY)")
        return 1
    
    print("\n=== 所有檢查通過，啟動伺服器 ===\n")
    
    # 啟動 Flask 伺服器
    try:
        subprocess.run([sys.executable, "app.py"], check=True)
    except KeyboardInterrupt:
        print("\n伺服器已停止")
    except Exception as e:
        print(f"✗ 伺服器啟動失敗: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
