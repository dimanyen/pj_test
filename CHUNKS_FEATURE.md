# 📚 Chunks 顯示功能說明

## 功能概述

在 searchVector 功能中新增了 chunks 顯示列表，讓用戶可以：
- 查看搜尋到的所有相關文檔片段
- 點擊片段查看詳細內容
- 了解每個片段的相關度分數和來源

## 新增功能

### 1. 後端 API 改進
- 修改 `/api/search` 端點，回傳完整的 chunks 資訊
- 新增 `chunks` 和 `total_chunks` 欄位
- 為每個 chunk 添加唯一 ID

### 2. 前端 UI 改進
- 新增「相關文檔片段」顯示區域
- 每個片段顯示：
  - 排名 (#1, #2, ...)
  - 相關度分數 (百分比)
  - 來源檔案路徑
  - 內容預覽 (前3行)
- 點擊片段可查看完整內容

### 3. 詳細內容彈窗
- 美觀的模態彈窗設計
- 顯示完整的文檔片段內容
- 支援鍵盤操作 (ESC 關閉)
- 點擊背景關閉

## 使用方式

1. **啟動伺服器**
   ```bash
   python app.py
   ```

2. **開啟瀏覽器**
   訪問 `http://localhost:5002`

3. **提問**
   - 在輸入框中輸入問題
   - 點擊「提問」按鈕或按 Enter

4. **查看結果**
   - 查看 AI 回答
   - 在回答下方查看「相關文檔片段」列表
   - 點擊任何片段查看詳細內容

## 技術實現

### 後端 (app.py)
```python
# 修改搜尋 API 回傳格式
return jsonify({
    'success': True,
    'query': query,
    'context': context,
    'results': results,
    'chunks': results,  # 新增
    'total_chunks': len(results)  # 新增
})
```

### 前端 (index.html)
- 新增 `displayChunks()` 函數顯示片段列表
- 新增 `showChunkDetail()` 函數顯示詳細內容
- 新增 `closeChunkModal()` 函數關閉彈窗
- 修改 `askQuestion()` 流程，在回答後顯示 chunks

## 樣式特色

- 響應式設計，支援手機和桌面
- 現代化的卡片式布局
- 平滑的動畫效果
- 直觀的視覺回饋

## 測試

執行測試腳本：
```bash
python test_chunks_feature.py
```

## 注意事項

- 確保知識庫索引已建立 (`python kb_rag.py build --folder knowledge_docs`)
- 確保 Flask 伺服器正常運行
- 建議使用現代瀏覽器以獲得最佳體驗
