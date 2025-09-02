from flask import Flask, request, jsonify, render_template_string, send_from_directory
from flask_cors import CORS
import os
import traceback
from kb_rag import ask, load_index

app = Flask(__name__)
# 啟用 CORS 以支援跨域請求
CORS(app)

# 全域變數來快取索引
_index = None
_chunks = None

def init_rag():
    """初始化 RAG 系統"""
    global _index, _chunks
    try:
        _index, _chunks = load_index()
        return True
    except Exception as e:
        print(f"[ERROR] RAG 初始化失敗: {e}")
        return False

# HTML 模板
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>知識庫問答系統</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Microsoft JhengHei', -apple-system, BlinkMacSystemFont, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 800px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        
        .header {
            background: linear-gradient(45deg, #ff6b6b, #4ecdc4);
            color: white;
            padding: 30px;
            text-align: center;
        }
        
        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        
        .header p {
            font-size: 1.1em;
            opacity: 0.9;
        }
        
        .content {
            padding: 40px;
        }
        
        .input-section {
            margin-bottom: 30px;
        }
        
        .input-group {
            display: flex;
            gap: 15px;
            margin-bottom: 20px;
        }
        
        .question-input {
            flex: 1;
            padding: 15px 20px;
            border: 2px solid #e0e0e0;
            border-radius: 25px;
            font-size: 16px;
            outline: none;
            transition: all 0.3s ease;
        }
        
        .question-input:focus {
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }
        
        .ask-btn {
            padding: 15px 30px;
            background: linear-gradient(45deg, #667eea, #764ba2);
            color: white;
            border: none;
            border-radius: 25px;
            font-size: 16px;
            font-weight: bold;
            cursor: pointer;
            transition: all 0.3s ease;
            white-space: nowrap;
        }
        
        .ask-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(102, 126, 234, 0.3);
        }
        
        .ask-btn:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
        }
        
        .loading {
            text-align: center;
            padding: 20px;
            color: #667eea;
            font-size: 18px;
        }
        
        .spinner {
            border: 3px solid #f3f3f3;
            border-top: 3px solid #667eea;
            border-radius: 50%;
            width: 30px;
            height: 30px;
            animation: spin 1s linear infinite;
            margin: 0 auto 15px;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        .answer-section {
            background: #f8f9fa;
            border-radius: 15px;
            padding: 25px;
            margin-top: 20px;
            min-height: 200px;
        }
        
        .answer-title {
            color: #2c3e50;
            font-size: 1.3em;
            margin-bottom: 15px;
            font-weight: bold;
        }
        
        .answer-content {
            color: #34495e;
            line-height: 1.6;
            font-size: 16px;
            white-space: pre-wrap;
        }
        
        .error {
            background: #fee;
            border: 1px solid #fcc;
            color: #c00;
            padding: 15px;
            border-radius: 8px;
            margin-top: 15px;
        }
        
        .status-indicator {
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 8px;
        }
        
        .status-ready {
            background-color: #4CAF50;
        }
        
        .status-error {
            background-color: #f44336;
        }
        
        .system-status {
            text-align: center;
            padding: 15px;
            background: #f0f0f0;
            font-size: 14px;
            color: #666;
        }
        
        @media (max-width: 768px) {
            .input-group {
                flex-direction: column;
            }
            
            .container {
                margin: 10px;
                border-radius: 10px;
            }
            
            .content {
                padding: 20px;
            }
            
            .header {
                padding: 20px;
            }
            
            .header h1 {
                font-size: 2em;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🧠 知識庫問答系統</h1>
            <p>基於 RAG 技術的智能問答助手</p>
        </div>
        
        <div class="content">
            <div class="system-status">
                <span class="status-indicator" id="statusIndicator"></span>
                <span id="statusText">檢查系統狀態中...</span>
            </div>
            
            <div class="input-section">
                <div class="input-group">
                    <input type="text" 
                           class="question-input" 
                           id="questionInput"
                           placeholder="請輸入您的問題..."
                           maxlength="500">
                    <button class="ask-btn" id="askBtn" onclick="askQuestion()">
                        提問
                    </button>
                </div>
            </div>
            
            <div class="answer-section">
                <div class="answer-title">💬 回答</div>
                <div class="answer-content" id="answerContent">
                    歡迎使用知識庫問答系統！請在上方輸入您的問題。
                </div>
            </div>
        </div>
    </div>

    <script>
        let isLoading = false;
        
        // 檢查系統狀態
        async function checkSystemStatus() {
            try {
                const response = await fetch('/api/status');
                const data = await response.json();
                
                const indicator = document.getElementById('statusIndicator');
                const statusText = document.getElementById('statusText');
                
                if (data.status === 'ready') {
                    indicator.className = 'status-indicator status-ready';
                    statusText.textContent = '系統就緒，可以開始提問';
                } else {
                    indicator.className = 'status-indicator status-error';
                    statusText.textContent = '系統未就緒：' + data.message;
                }
            } catch (error) {
                const indicator = document.getElementById('statusIndicator');
                const statusText = document.getElementById('statusText');
                indicator.className = 'status-indicator status-error';
                statusText.textContent = '無法連接到系統';
            }
        }
        
        // 提問函數
        async function askQuestion() {
            if (isLoading) return;
            
            const questionInput = document.getElementById('questionInput');
            const askBtn = document.getElementById('askBtn');
            const answerContent = document.getElementById('answerContent');
            
            const question = questionInput.value.trim();
            if (!question) {
                alert('請輸入問題！');
                return;
            }
            
            isLoading = true;
            askBtn.disabled = true;
            askBtn.textContent = '思考中...';
            
            // 顯示載入動畫
            answerContent.innerHTML = `
                <div class="loading">
                    <div class="spinner"></div>
                    正在查詢知識庫並生成回答...
                </div>
            `;
            
            try {
                // 設定 fetch timeout 為 120 秒
                const controller = new AbortController();
                const timeoutId = setTimeout(() => controller.abort(), 120000); // 120,000 ms = 120 秒

                let response;
                try {
                    response = await fetch('/api/ask', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({ question: question }),
                        signal: controller.signal
                    });
                } finally {
                    clearTimeout(timeoutId);
                }
                
                const data = await response.json();
                
                if (data.success) {
                    answerContent.textContent = data.answer;
                } else {
                    answerContent.innerHTML = `<div class="error">錯誤：${data.error}</div>`;
                }
                
            } catch (error) {
                answerContent.innerHTML = `<div class="error">網路錯誤：${error.message}</div>`;
            } finally {
                isLoading = false;
                askBtn.disabled = false;
                askBtn.textContent = '提問';
            }
        }
        
        // 按 Enter 鍵提問
        document.getElementById('questionInput').addEventListener('keypress', function(e) {
            if (e.key === 'Enter' && !isLoading) {
                askQuestion();
            }
        });
        
        // 頁面載入時檢查系統狀態
        window.onload = function() {
            checkSystemStatus();
        };
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    """主頁面 - 重定向到獨立的 HTML 檔案"""
    return send_from_directory('.', 'index.html')

@app.route('/embedded')
def embedded():
    """嵌入式頁面 - 使用原本的模板"""
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/status')
def status():
    """檢查系統狀態"""
    try:
        if _index is None:
            init_success = init_rag()
            if not init_success:
                return jsonify({
                    'status': 'error',
                    'message': '知識庫索引未建立，請先執行 python kb_rag.py build --folder knowledge_docs'
                })
        
        return jsonify({
            'status': 'ready',
            'message': '系統正常運行'
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        })

@app.route('/api/ask', methods=['POST'])
def api_ask():
    """問答 API 端點"""
    try:
        data = request.get_json()
        
        if not data or 'question' not in data:
            return jsonify({
                'success': False,
                'error': '請提供問題內容'
            }), 400
        
        question = data['question'].strip()
        if not question:
            return jsonify({
                'success': False,
                'error': '問題不能為空'
            }), 400
        
        # 確保 RAG 系統已初始化
        if _index is None:
            init_success = init_rag()
            if not init_success:
                return jsonify({
                    'success': False,
                    'error': '知識庫索引未建立，請先執行 python kb_rag.py build --folder knowledge_docs'
                }), 500
        
        # 呼叫 RAG 系統
        answer = ask(question)
        
        return jsonify({
            'success': True,
            'answer': answer,
            'question': question
        })
        
    except FileNotFoundError as e:
        return jsonify({
            'success': False,
            'error': '知識庫索引檔案不存在，請先建立索引'
        }), 500
    except Exception as e:
        print(f"[ERROR] API 錯誤: {e}")
        print(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': f'系統錯誤：{str(e)}'
        }), 500

@app.route('/api/health')
def health():
    """健康檢查端點"""
    return jsonify({
        'status': 'healthy',
        'service': '知識庫問答系統'
    })

if __name__ == '__main__':
    print("=== 知識庫問答系統啟動中 ===")
    print("系統檢查...")
    
    # 檢查是否有必要的檔案
    required_files = ['kb_rag.py']
    missing_files = [f for f in required_files if not os.path.exists(f)]
    
    if missing_files:
        print(f"[WARNING] 缺少檔案: {missing_files}")
    
    # 嘗試初始化 RAG 系統
    if init_rag():
        print("[OK] RAG 系統初始化成功")
    else:
        print("[WARNING] RAG 系統初始化失敗，需要先建立知識庫索引")
        print("請執行: python kb_rag.py build --folder knowledge_docs")
    
    print("\n=== 伺服器啟動 ===")
    print("網址: http://localhost:5002")
    print("API 文件:")
    print("  - GET  /              : 主頁面")
    print("  - GET  /api/status    : 系統狀態")
    print("  - POST /api/ask       : 問答 API")
    print("  - GET  /api/health    : 健康檢查")
    print("\n按 Ctrl+C 停止伺服器")
    
    app.run(debug=True, host='0.0.0.0', port=5002)
