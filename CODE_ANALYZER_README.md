# 程式碼分析工具

這是一個使用 LiteLLM API 進行程式碼分析的工具，支援分塊分析大型程式碼檔案並提供詳細的分析報告。

## 功能特色

- 支援分塊分析（預設每塊200行）
- 支援多種程式語言的分析
- 可自訂 prompt 模板
- 支援串流輸出模式
- 分析結果暫存機制
- 自動整理所有區塊分析結果
- **LLM 重新整理最終結果**（保持與原始格式一致）
- 可將分析結果保存至檔案
- 整合 LiteLLM API

## 安裝需求

確保已安裝必要的套件：

```bash
pip install openai
```

## 環境設定

設定環境變數（參考 kb_rag.py 的設定）：

```bash
export LITELLM_BASE=https://llm.cubeapp945566.work
export LITELLM_API_KEY=sk-GhYWCOAf9uCrYTioB_mohQ
```

## 使用方法

### 基本用法（分塊分析）

```bash
python code_analyzer.py --code your_code_file.py
```

### 自訂區塊大小

```bash
python code_analyzer.py --code your_code_file.py --chunk-size 300
```

### 使用自訂 prompt 模板

```bash
python code_analyzer.py --code your_code_file.py --prompt my_custom_prompt.txt
```

### 串流模式輸出

```bash
python code_analyzer.py --code your_code_file.py --stream
```

### 保存分析結果

```bash
python code_analyzer.py --code your_code_file.py --output analysis_result.txt
```

### 指定程式語言

```bash
python code_analyzer.py --code your_file.swift --language swift
```

### 分析完成後清理暫存檔案

```bash
python code_analyzer.py --code your_code_file.py --cleanup
```

### 僅整理現有暫存結果

```bash
python code_analyzer.py --code your_code_file.py --consolidate-only
```

### 使用 LLM 重新整理最終結果

```bash
python code_analyzer.py --code your_code_file.py --use-llm-consolidation
```

### 自訂整理 prompt 模板

```bash
python code_analyzer.py --code your_code_file.py --use-llm-consolidation --consolidation-prompt my_consolidation_prompt.txt
```

### 完整參數範例

```bash
python code_analyzer.py --code kb_rag.py --prompt prompt_template.txt --chunk-size 200 --language python --stream --output kb_rag_analysis.txt --use-llm-consolidation --cleanup
```

## 參數說明

- `--code`: 要分析的程式碼檔案路徑（必填）
- `--prompt`: prompt 模板檔案路徑（選填，預設為 prompt_template.txt）
- `--consolidation-prompt`: 整理 prompt 模板檔案路徑（選填，預設為 consolidation_prompt.txt）
- `--chunk-size`: 每個區塊的行數（選填，預設為 200）
- `--language`: 程式語言（選填，預設為 python）
- `--stream`: 使用串流模式輸出（選填）
- `--output`: 輸出檔案路徑（選填）
- `--cache-dir`: 暫存目錄（選填，預設為 analysis_cache）
- `--cleanup`: 分析完成後清理暫存檔案（選填）
- `--consolidate-only`: 僅整理現有的暫存結果（選填）
- `--use-llm-consolidation`: 使用 LLM 重新整理最終結果（選填）

## Prompt 模板

### 分析 Prompt 模板

預設的分析 prompt 模板檔案為 `prompt_template.txt`，您可以編輯此檔案來自訂分析內容。

模板中可以使用以下變數：
- `{FILE_PATH}`: 程式碼檔案路徑
- `{CHUNK_INDEX}`: 當前區塊索引（從1開始）
- `{TOTAL_CHUNKS}`: 總區塊數
- `{CODE_SNIPPET}`: 帶行號的程式碼內容

### 整理 Prompt 模板

預設的整理 prompt 模板檔案為 `consolidation_prompt.txt`，用於 LLM 重新整理最終結果。

模板中可以使用以下變數：
- `{FILE_NAME}`: 程式碼檔案名稱
- `{TOTAL_CHUNKS}`: 總區塊數
- `{CONSOLIDATED_RESULTS}`: 各區塊分析結果的原始內容

## 範例

### 分析 kb_rag.py 檔案（分塊分析）

```bash
python code_analyzer.py --code kb_rag.py --stream
```

這會將 kb_rag.py 分割為200行的區塊，逐一分析並以串流模式顯示結果。

### 分析大型檔案並保存結果

```bash
python code_analyzer.py --code large_file.py --chunk-size 300 --output analysis_report.md --cleanup
```

### 重新整理現有分析結果

```bash
python code_analyzer.py --code your_file.py --consolidate-only --output final_report.md
```

## 工作流程

1. **分塊處理**: 程式會將大型程式碼檔案分割為指定大小的區塊（預設200行）
2. **逐塊分析**: 每個區塊都會使用 LiteLLM API 進行分析
3. **結果暫存**: 每個區塊的分析結果會暫存在 `analysis_cache` 目錄中
4. **結果整理**: 所有區塊分析完成後，會自動整理成一份完整的分析報告
   - **簡單整理**: 直接合併各區塊結果（預設）
   - **LLM 整理**: 使用 LLM 重新整理，保持與原始格式一致（`--use-llm-consolidation`）
5. **清理暫存**: 可選擇在分析完成後清理暫存檔案

## 自訂 Prompt 範例

您可以建立自己的 prompt 模板，例如：

```
請分析以下程式碼區塊：

檔案：{FILE_PATH}
區塊：{CHUNK_INDEX}/{TOTAL_CHUNKS}

程式碼：
<<<CODE_START
{CODE_SNIPPET}
<<<CODE_END

請重點關注：
1. 程式碼的效能問題
2. 安全性漏洞
3. 可讀性改進建議

請用繁體中文回覆。
```

將此內容保存為 `my_prompt.txt`，然後使用：

```bash
python code_analyzer.py --code your_file.py --prompt my_prompt.txt
```
