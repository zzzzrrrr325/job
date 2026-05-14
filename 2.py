from flask import Flask, request, jsonify, render_template_string
from cozepy import Coze, TokenAuth, COZE_CN_BASE_URL, Message, ChatEventType, MessageObjectString
import time
import os
import tempfile

app = Flask(__name__)

# ====================== 配置 ======================
API_TOKEN = "pat_ZPcq6cxPqnI2F4cWL5D4m4Q3ZnDiakF4TdHzF9zhig4KZBmuTpRY9zII24vxOSdH"
BOT_ID = "7636990724844027913"

# 初始化 Coze 客户端
coze = Coze(auth=TokenAuth(token=API_TOKEN), base_url=COZE_CN_BASE_URL)
user_files = {}

# ====================== 网页模板 ======================
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>JobAgent - 智能求职助手</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            max-width: 900px;
            margin: 0 auto;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }
        .container {
            background: white;
            border-radius: 20px;
            padding: 30px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
        }
        h1 {
            color: #667eea;
            text-align: center;
            margin-bottom: 30px;
        }
        .upload-area {
            border: 2px dashed #667eea;
            border-radius: 10px;
            padding: 20px;
            text-align: center;
            margin: 20px 0;
            background: #f8f9ff;
        }
        .file-info {
            background: #e8f5e9;
            padding: 10px 15px;
            border-radius: 8px;
            margin: 10px 0;
            display: none;
            align-items: center;
            justify-content: space-between;
        }
        .chat-container {
            margin-top: 30px;
        }
        .message-area {
            background: #f7f8fa;
            border-radius: 10px;
            padding: 20px;
            min-height: 200px;
            max-height: 400px;
            overflow-y: auto;
            margin-bottom: 15px;
        }
        .message {
            margin-bottom: 15px;
            padding: 10px 15px;
            border-radius: 10px;
        }
        .user-message {
            background: #667eea;
            color: white;
            text-align: right;
            margin-left: 50px;
        }
        .bot-message {
            background: #e8eaf6;
            color: #333;
            margin-right: 50px;
        }
        .input-group {
            display: flex;
            gap: 10px;
        }
        textarea {
            flex: 1;
            padding: 12px;
            border: 1px solid #ddd;
            border-radius: 8px;
            font-size: 14px;
            resize: vertical;
            font-family: inherit;
        }
        button {
            background: #667eea;
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 14px;
            transition: all 0.3s;
        }
        button:hover {
            background: #5a67d8;
            transform: translateY(-1px);
        }
        button:disabled {
            background: #ccc;
            cursor: not-allowed;
            transform: none;
        }
        .status {
            margin-top: 10px;
            padding: 10px;
            border-radius: 5px;
            font-size: 14px;
        }
        .success { background: #c8e6c9; color: #2e7d32; }
        .error { background: #ffcdd2; color: #c62828; }
        .warning { background: #fff3e0; color: #ef6c00; }
        .typing {
            color: #999;
            font-style: italic;
            padding: 10px;
        }
        .clear-btn {
            background: #f44336;
            font-size: 12px;
            padding: 5px 10px;
        }
        .clear-btn:hover {
            background: #d32f2f;
        }
    </style>
</head>
<body>
    <div class="container">
    <!-- 在 container 内部顶部添加 -->
<div style="display: flex; justify-content: flex-end; margin-bottom: 15px;">
    <a href="http://localhost:8888" style="background: linear-gradient(135deg, #667eea, #764ba2); color: white; padding: 8px 20px; border-radius: 25px; text-decoration: none; font-weight: 500; display: inline-flex; align-items: center; gap: 8px;">
        🏠 返回首页
    </a>
</div>
        <h1>🤖 JobAgent 智能求职助手</h1>

        <div class="upload-area">
            <h3>📄 上传简历（PDF格式）</h3>
            <input type="file" id="fileInput" accept=".pdf">
            <button onclick="uploadResume()" style="margin-top: 10px;">上传简历</button>
            <div id="uploadStatus"></div>
        </div>

        <div id="fileInfo" class="file-info">
            <span id="fileName"></span>
            <button class="clear-btn" onclick="clearFile()">清除</button>
        </div>

        <div class="chat-container" id="chatArea" style="opacity:0.5; pointer-events:none;">
            <div class="message-area" id="messageArea">
                <div class="bot-message message">💡 请先上传您的简历，上传后我就可以帮您分析啦！</div>
            </div>
            <div class="input-group">
                <textarea id="question" placeholder="输入您的问题..." rows="2"></textarea>
                <button onclick="sendMessage()" id="sendBtn">发送</button>
            </div>
        </div>
    </div>

    <script>
        let fileId = null;
        let sessionId = 'session_' + Date.now();

        function scrollToBottom() {
            const area = document.getElementById('messageArea');
            area.scrollTop = area.scrollHeight;
        }

        function addMessage(text, isUser) {
            const area = document.getElementById('messageArea');
            const msgDiv = document.createElement('div');
            msgDiv.className = isUser ? 'user-message message' : 'bot-message message';
            msgDiv.innerHTML = (isUser ? '👤 ' : '🤖 ') + text.replace(/\\n/g, '<br>');
            area.appendChild(msgDiv);
            scrollToBottom();
        }

        function showTyping() {
            const area = document.getElementById('messageArea');
            const typingDiv = document.createElement('div');
            typingDiv.className = 'bot-message message typing';
            typingDiv.id = 'typingIndicator';
            typingDiv.innerHTML = '🤖 正在思考...';
            area.appendChild(typingDiv);
            scrollToBottom();
        }

        function hideTyping() {
            const typing = document.getElementById('typingIndicator');
            if (typing) typing.remove();
        }

        async function uploadResume() {
            const file = document.getElementById('fileInput').files[0];
            if (!file) {
                document.getElementById('uploadStatus').innerHTML = '<div class="status error">请选择PDF文件</div>';
                return;
            }

            const formData = new FormData();
            formData.append('file', file);
            formData.append('session_id', sessionId);

            document.getElementById('uploadStatus').innerHTML = '<div class="status warning">上传中...</div>';

            try {
                const response = await fetch('/upload', {
                    method: 'POST',
                    body: formData
                });
                const data = await response.json();

                if (data.code === 0) {
                    fileId = data.file_id;
                    document.getElementById('uploadStatus').innerHTML = '<div class="status success">✅ 上传成功！</div>';
                    document.getElementById('fileName').innerHTML = `📄 已上传: ${file.name}`;
                    document.getElementById('fileInfo').style.display = 'flex';
                    document.getElementById('chatArea').style.opacity = '1';
                    document.getElementById('chatArea').style.pointerEvents = 'auto';
                    addMessage('你好！简历已上传成功！我是专业求职全能助手✨，可以帮你：\\n- 上传简历做智能分析与优势评估\\n- 精准匹配并推荐招聘岗位\\n- 一键生成定制专属求职信\\n- 查询公司背景、行业趋势、面试攻略\\n\\n您可以向我提问了，比如：请分析我的简历优势、推荐适合我的岗位等。我来帮你全程搞定～', false);
                } else {
                    document.getElementById('uploadStatus').innerHTML = `<div class="status error">❌ ${data.msg}</div>`;
                }
            } catch (error) {
                document.getElementById('uploadStatus').innerHTML = `<div class="status error">❌ ${error.message}</div>`;
            }
        }

        function clearFile() {
            fileId = null;
            document.getElementById('fileInfo').style.display = 'none';
            document.getElementById('fileName').innerHTML = '';
            document.getElementById('uploadStatus').innerHTML = '<div class="status success">已清除简历</div>';
            document.getElementById('chatArea').style.opacity = '0.5';
            document.getElementById('chatArea').style.pointerEvents = 'none';
            addMessage('简历已清除，如需继续使用请重新上传简历。', false);
        }

        async function sendMessage() {
            const question = document.getElementById('question').value.trim();
            if (!question) {
                addMessage('请输入问题', true);
                return;
            }

            if (!fileId) {
                addMessage('请先上传简历再提问', false);
                return;
            }

            addMessage(question, true);
            document.getElementById('question').value = '';
            document.getElementById('sendBtn').disabled = true;
            showTyping();

            try {
                const response = await fetch('/chat', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        question: question,
                        file_id: fileId,
                        session_id: sessionId
                    })
                });
                const data = await response.json();

                hideTyping();

                if (data.code === 0) {
                    addMessage(data.answer, false);
                } else {
                    addMessage('❌ ' + data.msg, false);
                }
            } catch (error) {
                hideTyping();
                addMessage('❌ ' + error.message, false);
            } finally {
                document.getElementById('sendBtn').disabled = false;
            }
        }

        document.getElementById('question').addEventListener('keypress', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });
    </script>
</body>
</html>
"""


# ====================== 上传文件 ======================
@app.route('/upload', methods=['POST'])
def upload_file():
    """上传简历 - 使用 Coze SDK"""
    if 'file' not in request.files:
        return jsonify({'code': 400, 'msg': '没有文件'})

    file = request.files['file']
    if file.filename == '':
        return jsonify({'code': 400, 'msg': '文件名为空'})

    session_id = request.form.get('session_id', str(int(time.time())))
    temp_file_path = None

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
            file.save(temp_file.name)
            temp_file_path = temp_file.name

        with open(temp_file_path, 'rb') as f:
            file_obj = coze.files.upload(file=f)

        os.unlink(temp_file_path)
        user_files[session_id] = file_obj.id

        print(f"[DEBUG] Upload success, file_id: {file_obj.id}")
        return jsonify({'code': 0, 'file_id': file_obj.id})

    except Exception as e:
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.unlink(temp_file_path)
            except:
                pass

        print(f"[ERROR] Upload exception: {str(e)}")
        return jsonify({'code': 500, 'msg': f'上传失败: {str(e)}'})


# ====================== 对话接口 ======================
@app.route('/chat', methods=['POST'])
def chat():
    """发送对话 - 使用 Coze SDK 流式接口"""
    data = request.json
    question = data.get('question', '')
    file_id = data.get('file_id', '')
    session_id = data.get('session_id', str(int(time.time())))

    try:
        if file_id:
            message = Message.build_user_question_objects([
                MessageObjectString.build_text(question),
                MessageObjectString.build_file(file_id=file_id)
            ])
        else:
            message = Message.build_user_question_text(question)

        full_response = ""

        for event in coze.chat.stream(
                bot_id=BOT_ID,
                user_id=session_id,
                additional_messages=[message],
        ):
            if event.event == ChatEventType.CONVERSATION_MESSAGE_DELTA:
                full_response += event.message.content
            elif event.event == ChatEventType.CONVERSATION_CHAT_COMPLETED:
                print(f"[DEBUG] Chat completed, token usage: {event.chat.usage.token_count}")

        if full_response:
            return jsonify({'code': 0, 'answer': full_response})
        else:
            return jsonify({'code': 500, 'msg': '未收到回复内容'})

    except Exception as e:
        print(f"[ERROR] Chat exception: {str(e)}")
        return jsonify({'code': 500, 'msg': str(e)})


# ====================== 首页 ======================
@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)


# ====================== 启动 ======================
if __name__ == '__main__':
    print("=" * 60)
    print("🚀 JobAgent 服务启动 (SDK 版本)")
    print("📍 访问地址: http://127.0.0.1:5000")
    print("🤖 Bot ID: " + BOT_ID)
    print("=" * 60)
    # 修改为 debug=False 避免 Windows 信号问题
    app.run(host='127.0.0.1', port=5000, debug=False)