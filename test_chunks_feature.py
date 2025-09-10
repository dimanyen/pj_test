#!/usr/bin/env python3
"""
測試新的 chunk 切分功能
使用 --- 符號作為分段依據
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from kb_rag import chunk_text, CHUNK_SIZE

def test_chunk_splitting():
    """測試 chunk 切分功能"""
    
    # 測試資料 - 模擬您的文件格式
    test_text = """姓名: 顏勝洲
組別: -
工作項目: 米蟲
備註: 閒閒閒的人
---

姓名: 陳憶雯 Aki
組別: -
工作項目: 三雲A-A&Header格式統一 | IFX電文改打CDC(窗口) | BaNCS A-A /數位雲AA/資訊雲AA窗口
備註: 我是仙女
---

姓名: 李盈萱 Cyndi
組別: 大奶微微
工作項目: 移除舊版控/舊code
備註: 
---

姓名: 呂曜丞 Ray
組別: 大奶微微
工作項目: 小額跨境 | MMB英文版-總管理 | 英文版AI應用 | 外幣相關業務 | 外幣帳務：含外幣買賣、大額換匯 | 更多：台外幣>>外幣買賣 | 更多：台外幣>>外幣活存交易明細 | 更多：台外幣>>外匯匯入款項查詢及解匯 | 更多：台外幣>>App換匯紀錄 | 小額跨境(BU PM：姝榛) | 英文版AI應用_Beta team | 平台雙周會(借會議室+會通)
備註: 
---

姓名: 姚克翰 Falco
組別: 大奶微微
工作項目: 推播 | 友善金融 | 簡訊OTP | 更多：服務據點 | 更多：專屬優惠 | 交易驗證管理 | 登入 | 新增原住民姓名 (BU PM：產品科) | 啟用信用碼+裝置綁定FIDO (BU PM：仕錩)_車車 | L1服務開關建置 (系統維穩) | CommonDB 使用優化 (系統維穩) | DEMO/retro/Planning(借會議室+會通)
備註: 我有很多動物
---

姓名: 羅郁婷 Amanda
組別: 大奶微微
工作項目: 裝置綁定 | 兩步驟驗證 | 本行客戶英文戶名：長度調整為140字(BU PM：怡娟)_BBB | APP台幣轉帳功能顯示戶名(BU PM：瓊艷) | C3綜所稅臨調(BU PM：Stella)_車車 | 裝置綁定AA移轉(新url/帶APID)
備註: 
---

姓名: 吳泰宇
組別: 大奶微微
工作項目: FIDO快登 | 簡訊收件匣 | Passkey | OpenID &集保授權 | [FIDO2]3DS+Passkey | [無密碼]網銀FIDO登入 | [手機提款]強調主掃功能調整(BU PM：淇容)
備註: 
---

姓名: 彭怡娟
組別: 大奶微微
工作項目: (預計Q4接外幣維運) | IFX電文優化(評估改打CDC) | [數實+外幣開戶]黑名單阻擋加判斷失蹤人口
備註: 
---

姓名: 郭珉君
組別: 大奶微微
工作項目: 更多：服務據點 | 更多：專屬優惠 | 交易驗證管理 | 登入 | 新增原住民姓名 (BU PM：產品科) | 啟用信用碼+裝置綁定FIDO (BU PM：仕錩)_車車 | L1服務開關建置 (系統維穩) | CommonDB 使用優化 (系統維穩) | DEMO/retro/Planning(借會議室+會通)
備註: 我是仙女
---

姓名: 測試人員
組別: 測試組
工作項目: 這是一個很長的工作項目描述，用來測試當單個資料區塊超過 CHUNK_SIZE 時的處理情況。這個描述包含了大量的文字內容，目的是要讓這個區塊的大小超過設定的 CHUNK_SIZE 限制，以便測試我們的切分邏輯是否能夠正確處理這種情況。我們需要確保即使單個資料區塊很大，也能夠被正確地切分成多個較小的 chunk，同時保持資料的完整性和可讀性。
備註: 這是一個測試備註，用來驗證我們的切分功能是否能夠正確處理各種情況。
"""

    print(f"原始文本長度: {len(test_text)} 字元")
    print(f"CHUNK_SIZE 設定: {CHUNK_SIZE} 字元")
    print("=" * 60)
    
    # 執行 chunk 切分
    chunks = chunk_text(test_text)
    
    print(f"切分後共得到 {len(chunks)} 個 chunks:")
    print("=" * 60)
    
    for i, chunk in enumerate(chunks, 1):
        print(f"\n--- Chunk {i} (長度: {len(chunk)} 字元) ---")
        print(chunk)
        print(f"\n長度檢查: {'✓' if len(chunk) <= CHUNK_SIZE else '✗'} (限制: {CHUNK_SIZE})")
        print("-" * 40)
    
    # 統計資訊
    print(f"\n=== 統計資訊 ===")
    print(f"總 chunks 數: {len(chunks)}")
    print(f"平均 chunk 長度: {sum(len(c) for c in chunks) / len(chunks):.1f} 字元")
    print(f"最大 chunk 長度: {max(len(c) for c in chunks)} 字元")
    print(f"最小 chunk 長度: {min(len(c) for c in chunks)} 字元")
    
    # 檢查是否有超過限制的 chunk
    oversized_chunks = [i for i, c in enumerate(chunks) if len(c) > CHUNK_SIZE]
    if oversized_chunks:
        print(f"⚠️  發現 {len(oversized_chunks)} 個超過限制的 chunks: {oversized_chunks}")
    else:
        print("✅ 所有 chunks 都在大小限制內")

if __name__ == "__main__":
    test_chunk_splitting()