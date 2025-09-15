#!/usr/bin/env python3
"""
LLM 整理功能使用範例
"""

import os
import subprocess
import sys

def demonstrate_llm_consolidation():
    """展示 LLM 整理功能的使用"""
    print("=== LLM 整理功能使用範例 ===\n")
    
    # 檢查檔案是否存在
    if not os.path.exists("kb_rag.py"):
        print("錯誤：找不到 kb_rag.py 檔案")
        return False
    
    print("這個範例將展示如何使用 LLM 重新整理最終分析結果")
    print("LLM 整理功能會將各區塊的分析結果整合成統一的格式\n")
    
    print("1. 基本分析（不使用 LLM 整理）")
    print("命令：python3 code_analyzer.py --code kb_rag.py --output basic_analysis.md")
    print("結果：各區塊結果簡單合併\n")
    
    print("2. 使用 LLM 整理")
    print("命令：python3 code_analyzer.py --code kb_rag.py --use-llm-consolidation --output llm_analysis.md")
    print("結果：LLM 重新整理，保持與原始格式一致\n")
    
    print("3. 自訂整理 prompt")
    print("命令：python3 code_analyzer.py --code kb_rag.py --use-llm-consolidation --consolidation-prompt my_consolidation.txt")
    print("結果：使用自訂的整理 prompt\n")
    
    print("4. 僅整理現有結果")
    print("命令：python3 code_analyzer.py --code kb_rag.py --consolidate-only --use-llm-consolidation")
    print("結果：重新整理現有的暫存分析結果\n")
    
    # 詢問是否執行實際測試
    response = input("是否要執行實際測試？(y/N): ").strip().lower()
    if response == 'y':
        print("\n執行測試...")
        
        # 測試基本分析
        print("\n--- 執行基本分析 ---")
        try:
            result = subprocess.run([
                "python3", "code_analyzer.py",
                "--code", "kb_rag.py",
                "--chunk-size", "100",  # 小區塊以便快速測試
                "--output", "basic_analysis.md"
            ], capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                print("✓ 基本分析完成")
            else:
                print(f"✗ 基本分析失敗: {result.stderr}")
        except Exception as e:
            print(f"✗ 基本分析錯誤: {e}")
        
        # 測試 LLM 整理
        print("\n--- 執行 LLM 整理 ---")
        try:
            result = subprocess.run([
                "python3", "code_analyzer.py",
                "--code", "kb_rag.py",
                "--chunk-size", "100",
                "--use-llm-consolidation",
                "--output", "llm_analysis.md"
            ], capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                print("✓ LLM 整理完成")
                
                # 比較結果
                if os.path.exists("basic_analysis.md") and os.path.exists("llm_analysis.md"):
                    print("\n--- 結果比較 ---")
                    with open("basic_analysis.md", "r", encoding="utf-8") as f:
                        basic_content = f.read()
                    with open("llm_analysis.md", "r", encoding="utf-8") as f:
                        llm_content = f.read()
                    
                    print(f"基本分析長度: {len(basic_content)} 字元")
                    print(f"LLM 整理長度: {len(llm_content)} 字元")
                    print(f"LLM 整理結果預覽（前200字）:\n{llm_content[:200]}...")
            else:
                print(f"✗ LLM 整理失敗: {result.stderr}")
        except Exception as e:
            print(f"✗ LLM 整理錯誤: {e}")
        
        # 清理測試檔案
        test_files = ["basic_analysis.md", "llm_analysis.md"]
        for file in test_files:
            if os.path.exists(file):
                os.remove(file)
        
        # 清理暫存目錄
        if os.path.exists("analysis_cache"):
            import shutil
            shutil.rmtree("analysis_cache")
        
        print("\n✓ 測試完成！")
    else:
        print("跳過實際測試")

if __name__ == "__main__":
    demonstrate_llm_consolidation()
