from flask import Flask, request, jsonify, render_template_string, send_from_directory, Response, stream_with_context
from flask_cors import CORS
import os
import traceback
from kb_rag import ask, load_index, ask_stream

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


@app.route('/')
def index():
    """主頁面 - 重定向到獨立的 HTML 檔案"""
    return send_from_directory('.', 'index.html')


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
        
        # 是否使用串流
        stream_flag = False
        try:
            stream_flag = bool(data.get('stream', False))
        except Exception:
            stream_flag = False
        # 允許以 querystring 開啟：/api/ask?stream=true
        if not stream_flag:
            q = request.args.get('stream', '')
            stream_flag = str(q).lower() in ['1', 'true', 'yes']

        if not stream_flag:
            # 非串流：直接回傳完整答案
            answer = ask(question)
            return jsonify({
                'success': True,
                'answer': answer,
                'question': question
            })
        else:
            # 串流：以 NDJSON 逐步回傳
            def generate():
                import json
                # 開頭事件
                start_obj = {
                    'success': True,
                    'type': 'start',
                    'question': question
                }
                yield json.dumps(start_obj, ensure_ascii=False) + "\n"

                try:
                    for delta in ask_stream(question):
                        if not delta:
                            continue
                        yield json.dumps({'type': 'delta', 'content': delta}, ensure_ascii=False) + "\n"
                    # 結束事件
                    yield json.dumps({'type': 'end'}, ensure_ascii=False) + "\n"
                except Exception as e:
                    err = {'success': False, 'type': 'error', 'error': str(e)}
                    yield json.dumps(err, ensure_ascii=False) + "\n"

            headers = {
                'Cache-Control': 'no-cache',
                'X-Accel-Buffering': 'no'
            }
            return Response(stream_with_context(generate()), mimetype='application/x-ndjson; charset=utf-8', headers=headers)
        
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

@app.route('/api/search', methods=['POST'])
def api_search():
    """向量搜尋 API 端點"""
    try:
        data = request.get_json()
        
        if not data or 'query' not in data:
            return jsonify({
                'success': False,
                'error': '請提供查詢內容'
            }), 400
        
        from datetime import datetime
        today_str = datetime.now().strftime('%Y-%m-%d')
        query = f"{data['query'].strip()} #Today: {today_str}"
        if not query:
            return jsonify({
                'success': False,
                'error': '查詢不能為空'
            }), 400
        
        # 確保 RAG 系統已初始化
        if _index is None:
            init_success = init_rag()
            if not init_success:
                return jsonify({
                    'success': False,
                    'error': '知識庫索引未建立，請先執行 python kb_rag.py build --folder knowledge_docs'
                }), 500
        
        # 執行向量搜尋
        from kb_rag import search, format_context
        hits = search(_index, query, k=10)  # 使用 TOP_K=5
        context = format_context(hits)
        
        # 回傳搜尋結果
        results = []
        for rank, (chunk, score) in enumerate(hits, 1):
            results.append({
                'rank': rank,
                'score': float(score),
                'source': chunk.source,
                'text': chunk.text,
                'chunk_id': f"chunk_{rank}"  # 添加唯一 ID
            })
        
        return jsonify({
            'success': True,
            'query': query,
            'context': context,
            'results': results,
            'chunks': results,  # 添加 chunks 欄位，與 results 相同
            'total_chunks': len(results)
        })
        
    except Exception as e:
        print(f"[ERROR] 向量搜尋 API 錯誤: {e}")
        print(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': f'向量搜尋錯誤：{str(e)}'
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
