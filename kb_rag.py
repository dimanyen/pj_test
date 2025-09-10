import os
import json
import glob
import faiss
import argparse
from typing import List, Tuple, Dict
from dataclasses import dataclass

import numpy as np
from openai import OpenAI

# === 環境設定（指向 LiteLLM Proxy） =========================
# export LITELLM_BASE=https://llm.cubeapp945566.work
# export LITELLM_API_KEY=sk-local-123
BASE_URL = os.getenv("LITELLM_BASE", "https://llm.cubeapp945566.work")
API_KEY  = os.getenv("LITELLM_API_KEY", "sk-GhYWCOAf9uCrYTioB_mohQ")

# EMBEDDING_MODEL = "bge-m3"
EMBEDDING_MODEL = "intfloat-multilingual-e5-large"
# EMBEDDING_MODEL = "embeddinggemma"
CHAT_MODEL      = "gpt-oss-120b"

client = OpenAI(api_key=API_KEY, base_url=BASE_URL)

# === 參數建議 ==============================================
CHUNK_SIZE = 384
CHUNK_OVERLAP = 64
TOP_K = 10
INDEX_PATH = "kb.index"
STORE_PATH = "kb_store.jsonl"
SUMMARY_CACHE_PATH = "kb_summary_cache.json"

# 摘要相關參數
SUMMARY_MAX_TOKENS = 280          # 目標摘要長度（粗估 token，會由模型自行截斷）
SUMMARY_HEAD = "【文件摘要】"      # 放進每個 chunk 的前言標題
SUMMARY_SEPARATOR = "\n--- 以上為文件摘要 ---\n"
SUMMARY_PROMPT = (
    "你是嚴謹的技術文件摘要助手。請以繁體中文撰寫一段可供檢索前言使用的文件摘要，"
    "要求：\n"
    "1) 100~250字為佳（不需逐字對應原文；抓重點與名詞）\n"
    "2) 包含主題、目的、關鍵模組/名詞、可用查詢關鍵詞\n"
    "3) 不要使用條列符號，以短段落輸出\n"
)

# === 資料結構 ===============================================
@dataclass
class DocChunk:
    id: int
    text: str
    source: str

# === 工具：檔案與切塊 =======================================
def read_text_files(folder: str) -> List[Tuple[str, str]]:
    paths = glob.glob(os.path.join(folder, "**/*.txt"), recursive=True) + \
            glob.glob(os.path.join(folder, "**/*.md"), recursive=True)
    docs = []
    for p in paths:
        try:
            with open(p, "r", encoding="utf-8") as f:
                txt = f.read()
                if txt.strip():
                    docs.append((p, txt))
        except Exception as e:
            print(f"[WARN] 無法讀取 {p}: {e}")
    return docs

def chunk_text(text: str, size=CHUNK_SIZE, overlap=CHUNK_OVERLAP) -> List[str]:
    """
    使用 --- 符號作為分段依據來切分文本
    每個 chunk 會包含完整的資料區塊，且不超過指定大小
    """
    text = text.strip().replace("\r\n", "\n")
    
    # 使用 --- 符號分割文本
    sections = text.split("---")
    chunks = []
    current_chunk = ""
    
    for i, section in enumerate(sections):
        section = section.strip()
        if not section:
            continue
            
        # 如果當前 chunk 加上新 section 會超過大小限制
        if current_chunk and len(current_chunk) + len(section) + 5 > size:  # +5 for "\n---\n"
            # 保存當前 chunk
            chunks.append(current_chunk.strip())
            current_chunk = section
        else:
            # 將 section 加入當前 chunk
            if current_chunk:
                current_chunk += "\n---\n" + section
            else:
                current_chunk = section
    
    # 處理最後一個 chunk
    if current_chunk:
        chunks.append(current_chunk.strip())
    
    # 如果某個 chunk 仍然太大，需要進一步切分
    final_chunks = []
    for chunk in chunks:
        if len(chunk) <= size:
            final_chunks.append(chunk)
        else:
            # 對於過大的 chunk，使用滑動窗口方式切分
            start = 0
            while start < len(chunk):
                end = min(start + size, len(chunk))
                final_chunks.append(chunk[start:end])
                if end == len(chunk):
                    break
                start = end - overlap
                if start < 0:
                    start = 0
    
    return final_chunks

# === 工具：Embedding ========================================
def embed_texts(texts: List[str]) -> np.ndarray:
    resp = client.embeddings.create(model=EMBEDDING_MODEL, input=texts)
    vecs = [d.embedding for d in resp.data]
    return np.array(vecs, dtype="float32")

# === 工具：摘要（含快取） ===================================
def load_summary_cache() -> Dict[str, str]:
    if os.path.exists(SUMMARY_CACHE_PATH):
        try:
            with open(SUMMARY_CACHE_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_summary_cache(cache: Dict[str, str]):
    with open(SUMMARY_CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)

def safe_head(text: str, max_chars: int) -> str:
    return text.strip().replace("\r\n", " ").replace("\n", " ")[:max_chars]

def summarize_document(doc_text: str, source_path: str, cache: Dict[str, str]) -> str:
    # 以 source_path 當 key（若內容常變動，可改成內容 hash）
    if source_path in cache and cache[source_path].strip():
        return cache[source_path]

    # 控制輸入長度避免 prompt 過大（粗略取前 ~6000 字）
    doc_snippet = doc_text[:12000]

    try:
        messages = [
            {"role": "system", "content": "你是專業的技術與產品文件摘要助手。"},
            {
                "role": "user",
                "content": (
                    SUMMARY_PROMPT +
                    "\n\n以下為文件內容片段（可能非全文）：\n" +
                    doc_snippet
                )
            }
        ]
        resp = client.chat.completions.create(
            model=CHAT_MODEL,
            messages=messages,
            temperature=0.2
            
        )
        summary = resp.choices[0].message.content.strip()
        # 簡單清洗
        summary = summary.replace("\n\n", "\n").strip()
        if not summary:
            raise ValueError("空摘要")
    except Exception as e:
        print(f"[WARN] 產生摘要失敗，使用前置截斷作為摘要: {e}")
        summary = f"本文重點（自動截斷）：{safe_head(doc_text, 400)}"

    cache[source_path] = summary
    save_summary_cache(cache)
    return summary

def attach_summary_prefix(summary: str, chunk_text: str) -> str:
    # 將摘要作為前言，灌入每個 chunk
    prefix = f"{SUMMARY_HEAD}\n{summary}\n{SUMMARY_SEPARATOR}"
    return prefix + chunk_text

# === 建庫流程 ===============================================
def build_index(corpus_folder: str):
    print(f"[INFO] 掃描資料夾：{corpus_folder}")
    files = read_text_files(corpus_folder)
    if not files:
        print("[ERROR] 找不到任何 .txt/.md 檔案")
        return

    summary_cache = load_summary_cache()

    chunks: List[DocChunk] = []
    idx = 0

    # 逐檔：先摘要，再切塊，最後把摘要前言附加到每個 chunk
    for src, txt in files:
        print(f"[INFO] 摘要：{src}")
        doc_summary = summarize_document(txt, src, summary_cache)
        print(f"[INFO] 摘要：{doc_summary}")
        for ch in chunk_text(txt):
            combined = attach_summary_prefix(doc_summary, ch)
            chunks.append(DocChunk(id=idx, text=combined, source=src))
            idx += 1

    print(f"[INFO] 完成切塊（含摘要前綴），共 {len(chunks)} 片段。開始嵌入…（{EMBEDDING_MODEL}）")
    # 批次嵌入
    batch = 64
    all_vecs = []
    for i in range(0, len(chunks), batch):
        batch_texts = [c.text for c in chunks[i:i+batch]]
        vecs = embed_texts(batch_texts)
        all_vecs.append(vecs)
        print(f"  - 嵌入 {i} ~ {min(i+batch-1, len(chunks)-1)}")

    embs = np.vstack(all_vecs)
    dim = embs.shape[1]
    print(f"[INFO] 向量維度：{dim}")

    # 內積 + L2 normalize（對 bge 系列友善）
    faiss.normalize_L2(embs)
    index = faiss.IndexFlatIP(dim)
    index.add(embs)

    faiss.write_index(index, INDEX_PATH)
    save_store(chunks, STORE_PATH)
    print(f"[OK] 已建立索引：{INDEX_PATH}，儲存切塊對應：{STORE_PATH}")
    print(f"[OK] 摘要快取：{SUMMARY_CACHE_PATH}")

# === 檢索 + 生成 ===========================================
def load_store(path: str) -> List[DocChunk]:
    chunks = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            obj = json.loads(line)
            chunks.append(DocChunk(id=obj["id"], text=obj["text"], source=obj["source"]))
    return chunks

def save_store(chunks: List[DocChunk], path: str):
    with open(path, "w", encoding="utf-8") as f:
        for c in chunks:
            f.write(json.dumps({"id": c.id, "text": c.text, "source": c.source}, ensure_ascii=False) + "\n")

def load_index() -> Tuple[faiss.Index, List[DocChunk]]:
    if not (os.path.exists(INDEX_PATH) and os.path.exists(STORE_PATH)):
        raise FileNotFoundError("請先執行 build 建立知識庫索引（kb.index / kb_store.jsonl）。")
    index = faiss.read_index(INDEX_PATH)
    chunks = load_store(STORE_PATH)
    return index, chunks

def search(index: faiss.Index, query: str, k=TOP_K) -> List[Tuple[DocChunk, float]]:
    qv = embed_texts([query])
    faiss.normalize_L2(qv)
    scores, idxs = index.search(qv, k)
    idxs = idxs[0]
    scores = scores[0]
    store = load_store(STORE_PATH)
    results = []
    for i, s in zip(idxs, scores):
        if i == -1:  # faiss 若無結果會回 -1
            continue
        results.append((store[i], float(s)))
    return results

def format_context(results: List[Tuple[DocChunk, float]]) -> str:
    blocks = []
    for rank, (c, s) in enumerate(results, 1):
        blocks.append(f"[{rank}] (score={s:.4f}) source={c.source}\n{c.text}")
    return "\n\n---\n\n".join(blocks)

def ask(query: str) -> str:
    index, _ = load_index()
    hits = search(index, query, k=TOP_K)
    context = format_context(hits)

    system = (
        "你是嚴謹的技術助理。"
        "只根據提供的『檢索內容』回答；若無法從內容中找到答案，請明確說不知道並提出需要的資訊。"
        "回覆使用繁體中文，並在結尾列出引用片段的 [編號] 與 source 路徑。"
    )
    user = (
        f"查詢：{query}\n\n"
        f"檢索內容（依相關度排序；每段已含該文件摘要前言）：\n{context}\n\n"
        "請根據以上內容回答。若多處出現相同事實，優先以排名較前者為準。"
    )

    resp = client.chat.completions.create(
        model=CHAT_MODEL,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user}
        ],
        temperature=0.2
    )
    return resp.choices[0].message.content

def ask_stream(query: str):
    """串流問答：先檢索再以 Chat Completions stream 回傳增量內容。

    Yields:
        str: 回覆的增量文字（delta content）
    """
    index, _ = load_index()
    hits = search(index, query, k=TOP_K)
    context = format_context(hits)

    system = (
        "你是嚴謹的技術助理。"
        "只根據提供的『檢索內容』回答；若無法從內容中找到答案，請明確說不知道並提出需要的資訊。"
        "回覆使用繁體中文，並在結尾列出引用片段的 [編號] 與 source 路徑。"
    )
    user = (
        f"查詢：{query}\n\n"
        f"檢索內容（依相關度排序；每段已含該文件摘要前言）：\n{context}\n\n"
        "請根據以上內容回答。若多處出現相同事實，優先以排名較前者為準。"
    )

    stream = client.chat.completions.create(
        model=CHAT_MODEL,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user}
        ],
        temperature=0.2,
        stream=True
    )

    for chunk in stream:
        try:
            # openai>=1.0 ChatCompletionChunk
            delta = chunk.choices[0].delta.content or ""
        except Exception:
            delta = ""
        if delta:
            yield delta

# === CLI ==============================================
def main():
    parser = argparse.ArgumentParser(description="簡易 RAG 知識庫（LiteLLM + FAISS + 文件摘要前綴）")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_build = sub.add_parser("build", help="建立/覆蓋索引（含文件摘要前綴）")
    p_build.add_argument("--folder", required=True, help="知識庫資料夾（掃描 .txt/.md）")

    p_ask = sub.add_parser("ask", help="提出問題（需先 build）")
    p_ask.add_argument("--q", required=True, help="問題內容")

    args = parser.parse_args()

    if args.cmd == "build":
        build_index(args.folder)
    elif args.cmd == "ask":
        ans = ask(args.q)
        print("\n===== 答案 =====\n")
        print(ans)

if __name__ == "__main__":
    main()
