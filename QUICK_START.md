# 程式碼分析工具 - 快速開始指南

## 快速開始

### 1. 環境設定

確保已設定環境變數：

```bash
export LITELLM_BASE=https://llm.cubeapp945566.work
export LITELLM_API_KEY=sk-GhYWCOAf9uCrYTioB_mohQ
```

### 2. 基本使用

分析任何程式碼檔案：

```bash
python3 code_analyzer.py --code your_file.py
```

### 3. 常用命令

#### 分析並保存結果
```bash
python3 code_analyzer.py --code kb_rag.py --output analysis.md
```

#### 串流模式（即時顯示）
```bash
python3 code_analyzer.py --code kb_rag.py --stream
```

#### 自訂區塊大小
```bash
python3 code_analyzer.py --code large_file.py --chunk-size 300
```

#### 分析完成後清理暫存
```bash
python3 code_analyzer.py --code kb_rag.py --cleanup
```

#### 使用 LLM 重新整理最終結果
```bash
python3 code_analyzer.py --code kb_rag.py --use-llm-consolidation
```

### 4. 工作流程

1. **分塊**: 程式會將檔案分割為200行區塊（可自訂）
2. **分析**: 每個區塊都會使用 LLM 進行分析
3. **暫存**: 結果會暫存在 `analysis_cache` 目錄
4. **整理**: 所有區塊分析完成後自動整理成完整報告
   - **簡單整理**: 直接合併各區塊結果（預設）
   - **LLM 整理**: 使用 LLM 重新整理，保持格式一致（`--use-llm-consolidation`）
5. **清理**: 可選擇清理暫存檔案

### 5. 輸出格式

根據您的 `prompt_template.txt`，分析結果會包含：

- 檔案區塊分析
- 函式一覽（含參數、回傳值、副作用）
- 外部相依
- 函式關係圖
- 摘要

### 6. 自訂分析

編輯 `prompt_template.txt` 來自訂分析內容。模板支援以下變數：

- `{FILE_PATH}`: 檔案路徑
- `{CHUNK_INDEX}`: 區塊索引
- `{TOTAL_CHUNKS}`: 總區塊數
- `{CODE_SNIPPET}`: 帶行號的程式碼

### 7. 故障排除

- 如果分析中斷，可以使用 `--consolidate-only` 重新整理現有結果
- 暫存檔案位於 `analysis_cache` 目錄
- 使用 `--cleanup` 清理暫存檔案

### 8. 範例

查看 `example_usage.py` 了解完整使用範例：

```bash
python3 example_usage.py
```
