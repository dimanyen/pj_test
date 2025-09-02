# 知識庫問答系統

基於 Flask 和 RAG 技術的智能問答網站，整合了 `kb_rag.py` 的問答功能。

## 功能特色

- 🧠 **智能問答**: 使用 RAG (Retrieval-Augmented Generation) 技術
- 🎨 **現代化介面**: 響應式設計，支援桌面和行動裝置
- ⚡ **即時回應**: Ajax 異步請求，無需重新整理頁面
- 🔍 **知識庫檢索**: 自動從文件中找出最相關的內容
- 🛡️ **錯誤處理**: 完整的錯誤處理和使用者提示

## 快速開始

### 方法一：使用啟動腳本（推薦）

```bash
python start_server.py
```

啟動腳本會自動：
1. 檢查並安裝 Flask
2. 建立知識庫索引（如果不存在）
3. 啟動網站伺服器

### 方法二：手動啟動

1. **安裝依賴套件**:
```bash
pip install -r requirements.txt
```

2. **建立知識庫索引**（首次使用）:
```bash
python kb_rag.py build --folder knowledge_docs
```

3. **啟動網站**:
```bash
python app.py
```

## 訪問網站

啟動後訪問: http://localhost:5000

## API 端點

| 端點 | 方法 | 說明 |
|------|------|------|
| `/` | GET | 主頁面 |
| `/api/status` | GET | 檢查系統狀態 |
| `/api/ask` | POST | 問答 API |
| `/api/health` | GET | 健康檢查 |

### API 使用範例

**問答 API**:
```bash
curl -X POST http://localhost:5000/api/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "cubeapp 是什麼？"}'
```

**回應格式**:
```json
{
  "success": true,
  "answer": "根據文件內容...",
  "question": "cubeapp 是什麼？"
}
```

## 環境變數設定

確保設定以下環境變數（或使用預設值）：

```bash
export LITELLM_BASE=https://llm.cubeapp945566.work
export LITELLM_API_KEY=sk-local-123
```

## 檔案結構

```
pj_test/
├── app.py                 # Flask 主程式
├── kb_rag.py             # RAG 核心功能
├── start_server.py       # 啟動腳本
├── requirements.txt      # 依賴套件
├── knowledge_docs/       # 知識文件資料夾
├── kb.index             # FAISS 索引檔案（自動生成）
├── kb_store.jsonl       # 文件切塊儲存（自動生成）
└── kb_summary_cache.json # 摘要快取（自動生成）
```

## 疑難排解

**問題：知識庫索引建立失敗**
- 檢查 `knowledge_docs/` 資料夾是否存在且包含 .md 或 .txt 檔案
- 檢查網路連線和 API 金鑰設定

**問題：無法連接到語言模型**
- 確認環境變數 `LITELLM_BASE` 和 `LITELLM_API_KEY` 設定正確
- 檢查 LiteLLM 伺服器是否正常運行

**問題：Flask 導入錯誤**
- 執行 `pip install flask>=3.0.0`

## 自訂設定

可以在 `kb_rag.py` 中調整以下參數：
- `CHUNK_SIZE`: 文件切塊大小
- `TOP_K`: 檢索返回的相關文件數量
- `EMBEDDING_MODEL`: 嵌入模型
- `CHAT_MODEL`: 對話模型
