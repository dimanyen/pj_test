#!/usr/bin/env python3
"""
測試程式碼分析工具
"""

import os
import sys

def test_help():
    """測試幫助功能"""
    print("測試幫助功能...")
    os.system("python3 code_analyzer.py --help")

def test_small_file():
    """測試小檔案分析"""
    print("\n測試小檔案分析...")
    # 建立一個小的測試檔案
    test_code = '''def hello_world():
    """簡單的問候函數"""
    print("Hello, World!")

def add_numbers(a, b):
    """相加兩個數字"""
    return a + b

if __name__ == "__main__":
    hello_world()
    result = add_numbers(5, 3)
    print(f"5 + 3 = {result}")
'''
    
    with open("test_small.py", "w", encoding="utf-8") as f:
        f.write(test_code)
    
    print("執行分析...")
    os.system("python3 code_analyzer.py --code test_small.py --chunk-size 10 --output test_result.md")
    
    # 清理測試檔案
    if os.path.exists("test_small.py"):
        os.remove("test_small.py")
    if os.path.exists("test_result.md"):
        print("分析結果已保存至 test_result.md")
        with open("test_result.md", "r", encoding="utf-8") as f:
            print("結果預覽：")
            print(f.read()[:500] + "...")

if __name__ == "__main__":
    print("=== 程式碼分析工具測試 ===\n")
    
    # 測試幫助功能
    test_help()
    
    # 測試小檔案分析
    test_small_file()
    
    print("\n=== 測試完成 ===")
