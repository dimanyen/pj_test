#!/usr/bin/env python3
"""
程式碼分析工具使用範例
"""

import os
import subprocess
import sys

def run_analysis_example():
    """執行分析範例"""
    print("=== 程式碼分析工具使用範例 ===\n")
    
    # 檢查檔案是否存在
    if not os.path.exists("kb_rag.py"):
        print("錯誤：找不到 kb_rag.py 檔案")
        return
    
    if not os.path.exists("prompt_template.txt"):
        print("錯誤：找不到 prompt_template.txt 檔案")
        return
    
    print("1. 基本分析（分塊模式）")
    print("命令：python3 code_analyzer.py --code kb_rag.py")
    print("這會將 kb_rag.py 分割為200行的區塊進行分析\n")
    
    print("2. 自訂區塊大小")
    print("命令：python3 code_analyzer.py --code kb_rag.py --chunk-size 100")
    print("這會將 kb_rag.py 分割為100行的區塊進行分析\n")
    
    print("3. 串流模式分析")
    print("命令：python3 code_analyzer.py --code kb_rag.py --stream")
    print("這會以串流模式顯示分析結果\n")
    
    print("4. 保存分析結果")
    print("命令：python3 code_analyzer.py --code kb_rag.py --output kb_analysis.md")
    print("這會將分析結果保存至 kb_analysis.md\n")
    
    print("5. 分析完成後清理暫存")
    print("命令：python3 code_analyzer.py --code kb_rag.py --cleanup")
    print("這會分析完成後自動清理暫存檔案\n")
    
    print("6. 僅整理現有結果")
    print("命令：python3 code_analyzer.py --code kb_rag.py --consolidate-only")
    print("這會整理現有的暫存分析結果\n")
    
    # 詢問是否執行實際分析
    response = input("是否要執行實際分析？(y/N): ").strip().lower()
    if response == 'y':
        print("\n執行分析...")
        try:
            result = subprocess.run([
                "python3", "code_analyzer.py", 
                "--code", "kb_rag.py",
                "--output", "example_analysis.md",
                "--cleanup"
            ], capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                print("分析完成！結果已保存至 example_analysis.md")
                if os.path.exists("example_analysis.md"):
                    with open("example_analysis.md", "r", encoding="utf-8") as f:
                        content = f.read()
                        print(f"\n結果預覽（前500字）：\n{content[:500]}...")
            else:
                print(f"分析失敗：{result.stderr}")
        except subprocess.TimeoutExpired:
            print("分析超時（5分鐘）")
        except Exception as e:
            print(f"執行錯誤：{e}")
    else:
        print("跳過實際分析")

if __name__ == "__main__":
    run_analysis_example()
