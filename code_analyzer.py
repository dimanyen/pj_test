import os
import argparse
import json
from typing import Optional, List, Dict
from openai import OpenAI

# === 環境設定（指向 LiteLLM Proxy） =========================
BASE_URL = os.getenv("LITELLM_BASE", "https://llm.cubeapp945566.work")
API_KEY = os.getenv("LITELLM_API_KEY", "sk-GhYWCOAf9uCrYTioB_mohQ")
CHAT_MODEL = "gpt-oss-120b"

client = OpenAI(api_key=API_KEY, base_url=BASE_URL)

# === 工具函數 ===============================================
def read_code_file(file_path: str) -> str:
    """讀取程式碼檔案內容"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        return content
    except Exception as e:
        raise Exception(f"無法讀取檔案 {file_path}: {e}")

def split_code_into_chunks(code_content: str, chunk_size: int = 200) -> List[str]:
    """將程式碼分割成指定大小的區塊"""
    lines = code_content.split('\n')
    chunks = []
    
    for i in range(0, len(lines), chunk_size):
        chunk_lines = lines[i:i + chunk_size]
        chunk_content = '\n'.join(chunk_lines)
        chunks.append(chunk_content)
    
    return chunks

def add_line_numbers(code_content: str, start_line: int = 1) -> str:
    """為程式碼添加行號"""
    lines = code_content.split('\n')
    numbered_lines = []
    
    for i, line in enumerate(lines, start=start_line):
        numbered_lines.append(f"{i:4d}|{line}")
    
    return '\n'.join(numbered_lines)

def read_prompt_template(template_path: str) -> str:
    """讀取 prompt 模板檔案"""
    try:
        with open(template_path, "r", encoding="utf-8") as f:
            template = f.read()
        return template
    except Exception as e:
        raise Exception(f"無法讀取 prompt 模板 {template_path}: {e}")

def read_consolidation_prompt(template_path: str) -> str:
    """讀取整理 prompt 模板檔案"""
    try:
        with open(template_path, "r", encoding="utf-8") as f:
            template = f.read()
        return template
    except Exception as e:
        raise Exception(f"無法讀取整理 prompt 模板 {template_path}: {e}")

def analyze_code_chunk(code_chunk: str, prompt_template: str, file_name: str, 
                       chunk_index: int, total_chunks: int, language: str = "python") -> str:
    """使用 LiteLLM API 分析程式碼區塊"""
    try:
        # 為程式碼添加行號
        numbered_code = add_line_numbers(code_chunk, start_line=(chunk_index - 1) * 200 + 1)
        
        # 將程式碼內容插入到 prompt 模板中
        formatted_prompt = prompt_template.format(
            FILE_PATH=file_name,
            CHUNK_INDEX=chunk_index,
            TOTAL_CHUNKS=total_chunks,
            CODE_SNIPPET=numbered_code,
            language=language
        )
        
        messages = [
            {"role": "system", "content": "你是一個專業的程式碼分析師，擅長分析各種程式語言的程式碼。"},
            {"role": "user", "content": formatted_prompt}
        ]
        
        response = client.chat.completions.create(
            model=CHAT_MODEL,
            messages=messages,
            temperature=0.2
        )
        
        return response.choices[0].message.content.strip()
    except Exception as e:
        raise Exception(f"LLM API 呼叫失敗: {e}")

def analyze_code_chunk_stream(code_chunk: str, prompt_template: str, file_name: str, 
                             chunk_index: int, total_chunks: int, language: str = "python"):
    """使用串流方式分析程式碼區塊"""
    try:
        # 為程式碼添加行號
        numbered_code = add_line_numbers(code_chunk, start_line=(chunk_index - 1) * 200 + 1)
        
        # 將程式碼內容插入到 prompt 模板中
        formatted_prompt = prompt_template.format(
            FILE_PATH=file_name,
            CHUNK_INDEX=chunk_index,
            TOTAL_CHUNKS=total_chunks,
            CODE_SNIPPET=numbered_code,
            language=language
        )
        
        messages = [
            {"role": "system", "content": "你是一個專業的程式碼分析師，擅長分析各種程式語言的程式碼。"},
            {"role": "user", "content": formatted_prompt}
        ]
        
        stream = client.chat.completions.create(
            model=CHAT_MODEL,
            messages=messages,
            temperature=0.2,
            stream=True
        )
        
        for chunk in stream:
            try:
                delta = chunk.choices[0].delta.content or ""
            except Exception:
                delta = ""
            if delta:
                yield delta
    except Exception as e:
        raise Exception(f"LLM API 串流呼叫失敗: {e}")

def save_chunk_result(result: str, chunk_index: int, cache_dir: str = "analysis_cache"):
    """保存區塊分析結果"""
    os.makedirs(cache_dir, exist_ok=True)
    cache_file = os.path.join(cache_dir, f"chunk_{chunk_index:03d}.json")
    
    with open(cache_file, "w", encoding="utf-8") as f:
        json.dump({
            "chunk_index": chunk_index,
            "result": result,
            "timestamp": os.path.getctime(cache_file) if os.path.exists(cache_file) else None
        }, f, ensure_ascii=False, indent=2)

def load_chunk_results(cache_dir: str = "analysis_cache") -> List[Dict]:
    """載入所有區塊分析結果"""
    results = []
    if not os.path.exists(cache_dir):
        return results
    
    for filename in sorted(os.listdir(cache_dir)):
        if filename.startswith("chunk_") and filename.endswith(".json"):
            filepath = os.path.join(cache_dir, filename)
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    results.append(data)
            except Exception as e:
                print(f"[WARN] 無法載入 {filepath}: {e}")
    
    return sorted(results, key=lambda x: x["chunk_index"])

def consolidate_results(chunk_results: List[Dict], file_name: str, use_llm: bool = False, 
                       consolidation_prompt: str = None, language: str = "python") -> str:
    """將所有區塊分析結果整理成最終文件"""
    if not chunk_results:
        return "沒有找到任何分析結果。"
    
    if not use_llm:
        # 原始簡單整理方式
        consolidated = f"# {file_name} 完整程式碼分析報告\n\n"
        consolidated += f"## 檔案資訊\n"
        consolidated += f"- 檔案名稱: {file_name}\n"
        consolidated += f"- 分析區塊數: {len(chunk_results)}\n"
        consolidated += f"- 分析時間: {chunk_results[0].get('timestamp', 'unknown')}\n\n"
        
        # 合併所有區塊的分析結果
        for i, chunk_data in enumerate(chunk_results, 1):
            consolidated += f"## 區塊 {i} 分析結果\n\n"
            consolidated += chunk_data["result"]
            consolidated += "\n\n---\n\n"
        
        # 添加總結
        consolidated += "## 整體分析總結\n\n"
        consolidated += "以上是各區塊的詳細分析結果。每個區塊都包含了函式定義、外部相依、函式關係等資訊。\n"
        consolidated += "建議根據各區塊的分析結果，進一步整合和優化程式碼結構。\n"
        
        return consolidated
    
    # 使用 LLM 重新整理
    if not consolidation_prompt:
        raise ValueError("使用 LLM 整理時必須提供 consolidation_prompt")
    
    # 準備各區塊結果的原始內容
    chunk_contents = []
    for i, chunk_data in enumerate(chunk_results, 1):
        chunk_contents.append(f"=== 區塊 {i} 分析結果 ===\n{chunk_data['result']}\n")
    
    consolidated_raw = "\n".join(chunk_contents)
    
    # 計算總行數（估算）
    total_lines = len(chunk_results) * 200  # 假設每個區塊200行
    
    # 格式化 prompt
    formatted_prompt = consolidation_prompt.format(
        FILE_NAME=file_name,
        TOTAL_CHUNKS=len(chunk_results),
        CONSOLIDATED_RESULTS=consolidated_raw
    )
    
    try:
        messages = [
            {"role": "system", "content": "你是一個專業的程式碼分析結果整理器，擅長整合多個區塊的分析結果。"},
            {"role": "user", "content": formatted_prompt}
        ]
        
        response = client.chat.completions.create(
            model=CHAT_MODEL,
            messages=messages,
            temperature=0.2
        )
        
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"[WARN] LLM 整理失敗，使用原始整理方式: {e}")
        # 回退到原始整理方式
        return consolidate_results(chunk_results, file_name, use_llm=False)

def cleanup_cache(cache_dir: str = "analysis_cache"):
    """清理暫存檔案"""
    if os.path.exists(cache_dir):
        import shutil
        shutil.rmtree(cache_dir)
        print(f"[INFO] 已清理暫存目錄: {cache_dir}")

def main():
    parser = argparse.ArgumentParser(description="程式碼分析工具（使用 LiteLLM API，支援分塊分析）")
    parser.add_argument("--code", required=True, help="要分析的程式碼檔案路徑")
    parser.add_argument("--prompt", default="prompt_template.txt", help="prompt 模板檔案路徑（預設：prompt_template.txt）")
    parser.add_argument("--consolidation-prompt", default="consolidation_prompt.txt", help="整理 prompt 模板檔案路徑（預設：consolidation_prompt.txt）")
    parser.add_argument("--chunk-size", type=int, default=200, help="每個區塊的行數（預設：200）")
    parser.add_argument("--language", default="swift", help="程式語言（預設：python）")
    parser.add_argument("--stream", action="store_true", help="使用串流模式輸出")
    parser.add_argument("--output", help="輸出檔案路徑（可選）")
    parser.add_argument("--cache-dir", default="analysis_cache", help="暫存目錄（預設：analysis_cache）")
    parser.add_argument("--cleanup", action="store_true", help="分析完成後清理暫存檔案")
    parser.add_argument("--consolidate-only", action="store_true", help="僅整理現有的暫存結果")
    parser.add_argument("--use-llm-consolidation", default=True, action="store_true", help="使用 LLM 重新整理最終結果")
    
    args = parser.parse_args()
    
    try:
        # 如果只是要整理現有結果
        if args.consolidate_only:
            print(f"[INFO] 載入現有分析結果...")
            chunk_results = load_chunk_results(args.cache_dir)
            if not chunk_results:
                print("[ERROR] 沒有找到任何暫存的分析結果")
                return 1
            
            file_name = os.path.basename(args.code)
            
            # 讀取整理 prompt（如果需要）
            consolidation_prompt = None
            if args.use_llm_consolidation:
                print(f"[INFO] 讀取整理 prompt 模板：{args.consolidation_prompt}")
                consolidation_prompt = read_consolidation_prompt(args.consolidation_prompt)
            
            consolidated = consolidate_results(
                chunk_results, file_name, 
                use_llm=args.use_llm_consolidation,
                consolidation_prompt=consolidation_prompt,
                language=args.language
            )
            
            print("\n===== 整理後的分析結果 =====\n")
            print(consolidated)
            
            if args.output:
                with open(args.output, "w", encoding="utf-8") as f:
                    f.write(consolidated)
                print(f"\n[INFO] 結果已保存至：{args.output}")
            
            if args.cleanup:
                cleanup_cache(args.cache_dir)
            
            return 0
        
        # 讀取程式碼檔案
        print(f"[INFO] 讀取程式碼檔案：{args.code}")
        code_content = read_code_file(args.code)
        file_name = os.path.basename(args.code)
        
        # 讀取 prompt 模板
        print(f"[INFO] 讀取 prompt 模板：{args.prompt}")
        prompt_template = read_prompt_template(args.prompt)
        
        # 分割程式碼為區塊
        print(f"[INFO] 將程式碼分割為 {args.chunk_size} 行區塊...")
        code_chunks = split_code_into_chunks(code_content, args.chunk_size)
        total_chunks = len(code_chunks)
        print(f"[INFO] 共分割為 {total_chunks} 個區塊")
        
        # 分析每個區塊
        for i, chunk in enumerate(code_chunks, 1):
            print(f"\n[INFO] 分析區塊 {i}/{total_chunks}...")
            
            if args.stream:
                print(f"\n===== 區塊 {i} 分析結果 =====\n")
                output_content = ""
                for delta in analyze_code_chunk_stream(chunk, prompt_template, file_name, i, total_chunks, args.language):
                    print(delta, end="", flush=True)
                    output_content += delta
                print("\n")
                
                # 保存區塊結果
                save_chunk_result(output_content, i, args.cache_dir)
            else:
                result = analyze_code_chunk(chunk, prompt_template, file_name, i, total_chunks, args.language)
                print(f"\n===== 區塊 {i} 分析結果 =====\n")
                print(result)
                
                # 保存區塊結果
                save_chunk_result(result, i, args.cache_dir)
        
        # 載入所有區塊結果並整理
        print(f"\n[INFO] 整理所有區塊分析結果...")
        chunk_results = load_chunk_results(args.cache_dir)
        
        # 讀取整理 prompt（如果需要）
        consolidation_prompt = None
        if args.use_llm_consolidation:
            print(f"[INFO] 讀取整理 prompt 模板：{args.consolidation_prompt}")
            consolidation_prompt = read_consolidation_prompt(args.consolidation_prompt)
        
        consolidated = consolidate_results(
            chunk_results, file_name,
            use_llm=args.use_llm_consolidation,
            consolidation_prompt=consolidation_prompt,
            language=args.language
        )
        
        print("\n===== 完整分析結果 =====\n")
        print(consolidated)
        
        # 如果指定了輸出檔案，則保存結果
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(consolidated)
            print(f"\n[INFO] 完整結果已保存至：{args.output}")
        
        # 清理暫存檔案
        if args.cleanup:
            cleanup_cache(args.cache_dir)
                
    except Exception as e:
        print(f"[ERROR] {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
