#!/usr/bin/env python3
"""
測試 LLM 整理功能
"""

import os
import subprocess
import sys

def test_consolidation():
    """測試 LLM 整理功能"""
    print("=== 測試 LLM 整理功能 ===\n")
    
    # 檢查必要檔案
    required_files = ["code_analyzer.py", "prompt_template.txt", "consolidation_prompt.txt"]
    for file in required_files:
        if not os.path.exists(file):
            print(f"錯誤：找不到 {file}")
            return False
    
    # 建立測試程式碼
    test_code = '''def hello_world():
    """簡單的問候函數"""
    print("Hello, World!")

def add_numbers(a, b):
    """相加兩個數字"""
    return a + b

def multiply_numbers(x, y):
    """相乘兩個數字"""
    return x * y

if __name__ == "__main__":
    hello_world()
    result = add_numbers(5, 3)
    print(f"5 + 3 = {result}")
    product = multiply_numbers(4, 6)
    print(f"4 * 6 = {product}")
'''
    
    # 寫入測試檔案
    with open("test_consolidation.py", "w", encoding="utf-8") as f:
        f.write(test_code)
    
    print("1. 測試基本分析（不使用 LLM 整理）")
    try:
        result = subprocess.run([
            "python3", "code_analyzer.py",
            "--code", "test_consolidation.py",
            "--chunk-size", "5",  # 小區塊以便測試
            "--output", "test_basic.md"
        ], capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            print("✓ 基本分析完成")
        else:
            print(f"✗ 基本分析失敗: {result.stderr}")
            return False
    except Exception as e:
        print(f"✗ 基本分析錯誤: {e}")
        return False
    
    print("\n2. 測試 LLM 整理功能")
    try:
        result = subprocess.run([
            "python3", "code_analyzer.py",
            "--code", "test_consolidation.py",
            "--chunk-size", "5",
            "--use-llm-consolidation",
            "--output", "test_llm_consolidated.md"
        ], capture_output=True, text=True, timeout=120)
        
        if result.returncode == 0:
            print("✓ LLM 整理完成")
        else:
            print(f"✗ LLM 整理失敗: {result.stderr}")
            return False
    except Exception as e:
        print(f"✗ LLM 整理錯誤: {e}")
        return False
    
    print("\n3. 測試僅整理現有結果")
    try:
        result = subprocess.run([
            "python3", "code_analyzer.py",
            "--code", "test_consolidation.py",
            "--consolidate-only",
            "--use-llm-consolidation",
            "--output", "test_consolidate_only.md"
        ], capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            print("✓ 僅整理功能完成")
        else:
            print(f"✗ 僅整理功能失敗: {result.stderr}")
            return False
    except Exception as e:
        print(f"✗ 僅整理功能錯誤: {e}")
        return False
    
    # 清理測試檔案
    test_files = ["test_consolidation.py", "test_basic.md", "test_llm_consolidated.md", "test_consolidate_only.md"]
    for file in test_files:
        if os.path.exists(file):
            os.remove(file)
    
    # 清理暫存目錄
    if os.path.exists("analysis_cache"):
        import shutil
        shutil.rmtree("analysis_cache")
    
    print("\n✓ 所有測試完成！")
    return True

if __name__ == "__main__":
    success = test_consolidation()
    sys.exit(0 if success else 1)
