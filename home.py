# home.py - 无弹窗版本
from flask import Flask, render_template_string, redirect, request
import webbrowser
import threading
import time

app = Flask(__name__)

# ====================== 首页模板 ======================
HOME_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>JobAgent 智能求职中枢 | 选择您的助手</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:opsz,wght@14..32,300;14..32,400;14..32,500;14..32,600;14..32,700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Inter', 'Segoe UI', system-ui, -apple-system, 'PingFang SC', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            position: relative;
            overflow-x: hidden;
        }

        .bg-animation {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            z-index: 0;
            overflow: hidden;
        }

        .bg-animation .circle {
            position: absolute;
            border-radius: 50%;
            background: rgba(255, 255, 255, 0.1);
            animation: float 20s infinite ease-in-out;
        }

        .bg-animation .circle:nth-child(1) {
            width: 300px;
            height: 300px;
            top: -100px;
            left: -100px;
            animation-delay: 0s;
        }

        .bg-animation .circle:nth-child(2) {
            width: 500px;
            height: 500px;
            bottom: -150px;
            right: -150px;
            animation-delay: -5s;
        }

        .bg-animation .circle:nth-child(3) {
            width: 200px;
            height: 200px;
            top: 50%;
            left: 20%;
            animation-delay: -10s;
        }

        .bg-animation .circle:nth-child(4) {
            width: 400px;
            height: 400px;
            bottom: 20%;
            right: 10%;
            animation-delay: -15s;
        }

        @keyframes float {
            0%, 100% { transform: translateY(0) translateX(0) rotate(0deg); }
            33% { transform: translateY(-30px) translateX(20px) rotate(120deg); }
            66% { transform: translateY(30px) translateX(-20px) rotate(240deg); }
        }

        .portal {
            position: relative;
            z-index: 2;
            max-width: 1400px;
            width: 100%;
            margin: 0 auto;
            padding: 2rem;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
        }

        .hero {
            text-align: center;
            margin-bottom: 4rem;
            animation: fadeInUp 0.8s ease-out;
        }

        .hero h1 {
            font-size: 3.5rem;
            font-weight: 800;
            background: linear-gradient(135deg, #ffffff 0%, #f0f0ff 100%);
            background-clip: text;
            -webkit-background-clip: text;
            color: transparent;
            margin-bottom: 1rem;
        }

        .hero-badge {
            background: rgba(255, 255, 255, 0.2);
            backdrop-filter: blur(10px);
            padding: 0.5rem 1.5rem;
            border-radius: 60px;
            font-size: 0.9rem;
            font-weight: 600;
            color: white;
            display: inline-block;
            margin-bottom: 1.5rem;
            border: 1px solid rgba(255,255,255,0.3);
        }

        .hero p {
            font-size: 1.2rem;
            color: rgba(255, 255, 255, 0.9);
            max-width: 600px;
            margin: 0.5rem auto 0;
        }

        .cards-grid {
            display: flex;
            flex-wrap: wrap;
            gap: 2.5rem;
            justify-content: center;
            margin: 1rem 0 3rem;
        }

        .card {
            background: rgba(255, 255, 255, 0.98);
            backdrop-filter: blur(10px);
            border-radius: 2rem;
            box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
            padding: 2rem 2rem;
            width: 360px;
            transition: all 0.4s cubic-bezier(0.2, 0.9, 0.4, 1.1);
            border: 1px solid rgba(255,255,255,0.5);
            cursor: pointer;
            display: flex;
            flex-direction: column;
            position: relative;
            overflow: hidden;
        }

        .card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 4px;
            background: linear-gradient(90deg, #667eea, #764ba2);
            transform: scaleX(0);
            transition: transform 0.3s ease;
        }

        .card:hover::before {
            transform: scaleX(1);
        }

        .card:hover {
            transform: translateY(-12px);
            box-shadow: 0 35px 60px -15px rgba(0, 0, 0, 0.3);
            background: white;
        }

        .card-icon {
            font-size: 4rem;
            margin-bottom: 1rem;
            background: linear-gradient(135deg, #667eea20, #764ba220);
            width: 80px;
            height: 80px;
            display: flex;
            align-items: center;
            justify-content: center;
            border-radius: 30px;
            transition: 0.3s;
        }

        .card:hover .card-icon {
            transform: scale(1.05) rotate(5deg);
        }

        .card h2 {
            font-size: 1.8rem;
            font-weight: 700;
            margin: 0.75rem 0 0.5rem;
            background: linear-gradient(135deg, #1F2B48, #2c3e66);
            background-clip: text;
            -webkit-background-clip: text;
            color: transparent;
        }

        .badge-local {
            background: linear-gradient(135deg, #e6f0ff, #d4e4ff);
            color: #1e6fdf;
            font-size: 0.7rem;
            font-weight: 700;
            padding: 0.3rem 1rem;
            border-radius: 30px;
            width: fit-content;
            margin: 0.5rem 0 0.8rem;
        }

        .badge-coze {
            background: linear-gradient(135deg, #f2e6ff, #e8d9ff);
            color: #8b5cf6;
            font-size: 0.7rem;
            font-weight: 700;
            padding: 0.3rem 1rem;
            border-radius: 30px;
            width: fit-content;
            margin: 0.5rem 0 0.8rem;
        }

        .card p {
            color: #4b5563;
            line-height: 1.6;
            margin: 0.5rem 0 1rem;
            font-size: 0.95rem;
        }

        .feature-list {
            margin: 0.75rem 0 1.5rem;
            list-style: none;
            padding: 0;
        }

        .feature-list li {
            font-size: 0.85rem;
            padding: 0.4rem 0;
            display: flex;
            align-items: center;
            gap: 10px;
            color: #4a5568;
        }

        .feature-list li i {
            width: 20px;
            color: #667eea;
            font-size: 0.9rem;
        }

        .btn-choose {
            background: linear-gradient(135deg, #667eea, #764ba2);
            border: none;
            padding: 0.85rem 0;
            border-radius: 2rem;
            font-weight: 700;
            font-size: 1rem;
            margin-top: auto;
            cursor: pointer;
            transition: all 0.3s;
            color: white;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 0.75rem;
            width: 100%;
            font-family: inherit;
            box-shadow: 0 4px 12px rgba(102,126,234,0.3);
        }

        .btn-choose:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(102,126,234,0.4);
        }

        .info-panel {
            background: rgba(255, 255, 255, 0.2);
            backdrop-filter: blur(10px);
            border-radius: 2rem;
            padding: 1.5rem 2rem;
            margin-top: 2rem;
            display: flex;
            flex-wrap: wrap;
            justify-content: space-between;
            align-items: center;
            gap: 1rem;
            border: 1px solid rgba(255,255,255,0.3);
        }

        .status-dot {
            display: inline-block;
            width: 10px;
            height: 10px;
            border-radius: 10px;
            background-color: #2bdd4e;
            box-shadow: 0 0 0 2px rgba(43,221,78,0.3);
            margin-right: 8px;
            animation: pulse 2s infinite;
        }

        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.6; }
        }

        .check-service {
            display: flex;
            gap: 1.5rem;
            color: white;
            font-weight: 500;
        }

        .help-text {
            font-size: 0.85rem;
            color: rgba(255,255,255,0.8);
        }

        @keyframes fadeInUp {
            from {
                opacity: 0;
                transform: translateY(30px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        @media (max-width: 780px) {
            .portal {
                padding: 1rem;
            }
            .hero h1 {
                font-size: 2.2rem;
            }
            .card {
                width: 100%;
                max-width: 380px;
            }
            .check-service {
                flex-direction: column;
                gap: 0.5rem;
            }
        }

        .toast-msg {
            position: fixed;
            bottom: 100px;
            left: 50%;
            transform: translateX(-50%) scale(0.9);
            background: rgba(0, 0, 0, 0.9);
            backdrop-filter: blur(12px);
            color: white;
            padding: 12px 24px;
            border-radius: 60px;
            font-size: 0.9rem;
            opacity: 0;
            transition: 0.2s;
            pointer-events: none;
            z-index: 999;
            font-weight: 500;
            white-space: nowrap;
        }
    </style>
</head>
<body>
<div class="bg-animation">
    <div class="circle"></div>
    <div class="circle"></div>
    <div class="circle"></div>
    <div class="circle"></div>
</div>

<div class="portal">
    <div class="hero">
        <div class="hero-badge">
            <i class="fas fa-robot"></i> 多智能体 · 双擎驱动
        </div>
        <h1>
            <i class="fas fa-briefcase"></i> JobAgent 智能求职中枢
        </h1>
        <p>选择您偏好的智能体服务，开启智能求职之旅</p>
    </div>

    <div class="cards-grid">
        <div class="card" onclick="window.location.href='http://localhost:8501'">
            <div class="card-icon">
                <i class="fas fa-code-branch"></i>
            </div>
            <h2>JobAgent MultiAgent</h2>
            <div class="badge-local">
                <i class="fas fa-server"></i> 本地企业级 · LangGraph 引擎
            </div>
            <p>基于 LangGraph 的多智能体协作系统，深度分析简历，全网岗位挖掘，定制求职信生成。</p>
            <ul class="feature-list">
                <li><i class="fas fa-file-alt"></i> 智能简历解析 + 优势评估</li>
                <li><i class="fas fa-search"></i> Serper / Firecrawl 实时岗位搜索</li>
                <li><i class="fas fa-envelope"></i> 一键生成定制求职信</li>
                <li><i class="fas fa-building"></i> 公司背景调研 / 行业趋势</li>
                <li><i class="fas fa-brain"></i> 多Agent智能编排</li>
            </ul>
            <button class="btn-choose">
                <i class="fas fa-rocket"></i> 启动本地助手
                <i class="fas fa-arrow-right"></i>
            </button>
            <div class="help-text" style="margin-top: 12px; text-align: center; color: #6c757d;">
                <i class="fas fa-plug"></i> 端口: 8501 (Streamlit)
            </div>
        </div>

        <div class="card" onclick="window.location.href='http://localhost:5000'">
            <div class="card-icon">
                <i class="fas fa-cloud-upload-alt"></i>
            </div>
            <h2>Coze 智能求职助手</h2>
            <div class="badge-coze">
                <i class="fas fa-cloud"></i> 云端 Bot · Coze 引擎
            </div>
            <p>依托 Coze 平台的高效对话机器人，集成简历解析 + 智能问答，快速响应求职需求。</p>
            <ul class="feature-list">
                <li><i class="fas fa-file-pdf"></i> 极速PDF简历上传 + 安全存储</li>
                <li><i class="fas fa-lightbulb"></i> 预设求职场景: 岗位推荐 / 面试攻略</li>
                <li><i class="fas fa-comments"></i> 流式对话响应，体验流畅</li>
                <li><i class="fas fa-chart-line"></i> 轻量化部署，无需本地环境</li>
                <li><i class="fas fa-clock"></i> 7x24h 智能问答</li>
            </ul>
            <button class="btn-choose">
                <i class="fas fa-cloud-upload-alt"></i> 连接扣子助手
                <i class="fas fa-arrow-right"></i>
            </button>
            <div class="help-text" style="margin-top: 12px; text-align: center; color: #6c757d;">
                <i class="fas fa-plug"></i> 端口: 5000 (Flask)
            </div>
        </div>
    </div>

    <div class="info-panel">
        <div class="check-service">
            <span><i class="fas fa-circle"></i> 服务状态</span>
            <span id="localStatus">
                <span class="status-dot"></span> 检测中...
            </span>
            <span id="cozeStatus">
                <span class="status-dot"></span> 检测中...
            </span>
        </div>
        <div class="help-text">
            <i class="fas fa-info-circle"></i> 点击卡片直接跳转
        </div>
    </div>
</div>

<script>
    // 只用于显示状态，不进行任何跳转检查
    async function checkLocal() {
        try {
            await fetch('http://localhost:8501', { method: 'HEAD', mode: 'no-cors', cache: 'no-cache' });
            document.getElementById('localStatus').innerHTML = '<span class="status-dot" style="background:#2bdd4e;"></span> 本地 ✅ 运行中';
        } catch(e) {
            document.getElementById('localStatus').innerHTML = '<span class="status-dot" style="background:#ef4444;"></span> 本地 ❌ 未启动';
        }
    }

    async function checkCoze() {
        try {
            const res = await fetch('http://localhost:5000', { method: 'GET', cache: 'no-cache' });
            if (res.ok || res.status === 200) {
                document.getElementById('cozeStatus').innerHTML = '<span class="status-dot" style="background:#2bdd4e;"></span> Coze ✅ 运行中';
            } else {
                throw new Error();
            }
        } catch(e) {
            document.getElementById('cozeStatus').innerHTML = '<span class="status-dot" style="background:#ef4444;"></span> Coze ❌ 未启动';
        }
    }

    // 只更新显示状态，不影响跳转
    checkLocal();
    checkCoze();
    setInterval(() => { checkLocal(); checkCoze(); }, 30000);
</script>
</body>
</html>
"""


@app.route('/')
def index():
    return render_template_string(HOME_TEMPLATE)


if __name__ == '__main__':
    print("=" * 70)
    print("🏠 JobAgent 统一入口首页 (无弹窗版)")
    print("📍 访问地址: http://127.0.0.1:8888")
    print("=" * 70)
    print("📌 提示：")
    print("  - 本地服务: http://localhost:8501")
    print("  - Coze服务: http://localhost:5000")
    print("  - 点击卡片直接跳转，无弹窗！")
    print("=" * 70)

    def open_browser():
        time.sleep(1.5)
        webbrowser.open('http://127.0.0.1:8888')

    threading.Thread(target=open_browser, daemon=True).start()
    app.run(host='127.0.0.1', port=8888, debug=False, threaded=True)