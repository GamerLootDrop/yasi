import streamlit as st
import json
from openai import OpenAI
from datetime import datetime

# 1. 强制覆盖并接管 Streamlit 的原生样式，达到 100% 全屏无边界 HTML 体验
st.set_page_config(
    page_title="IELTS AI Examiner Pro - Dashboard",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 隐藏 Streamlit 原生的头部、底部和内边距，使我们自定义的高端前端占满整个浏览器视口
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    .block-container {
        padding: 0px !important;
        margin: 0px !important;
        max-width: 100% !important;
        height: 100vh !important;
    }
    iframe {
        position: fixed;
        top: 0;
        left: 0;
        width: 100vw;
        height: 100vh;
        border: none;
        margin: 0;
        padding: 0;
        overflow: hidden;
        z-index: 999999;
    }
    </style>
""", unsafe_allow_html=True)

# 2. 从 Secrets 中读取 API 配置
API_KEY = st.secrets.get("LLM_API_KEY", "")
BASE_URL = st.secrets.get("LLM_BASE_URL", "https://api.deepseek.com/v1")

# 3. 核心单页 HTML/CSS/JS 前端应用代码（已完美修复中英文排版、下拉框样式与字体突兀问题）
html_code = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>雅思 AI 助教 Pro 平台</title>
    <style>
        /* 全局现代高端中英文通用字体，彻底解决英文/数字突兀、变宋体的问题 */
        * {{
            box-sizing: border-box;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, "PingFang SC", "Microsoft YaHei", sans-serif;
        }}
        body, html {{
            margin: 0;
            padding: 0;
            width: 100%;
            height: 100%;
            background-color: #f8fafc;
            color: #1e293b;
            overflow: hidden;
        }}
        .app-container {{
            display: flex;
            width: 100vw;
            height: 100vh;
        }}
        /* 左侧固定的高级侧边栏 */
        .sidebar {{
            width: 260px;
            background: linear-gradient(180deg, #1e293b 0%, #0f172a 100%);
            color: #94a3b8;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            padding: 24px 16px;
            box-shadow: 4px 0 20px rgba(0,0,0,0.05);
            z-index: 10;
        }}
        .brand {{
            display: flex;
            align-items: center;
            gap: 12px;
            color: #ffffff;
            font-size: 18px;
            font-weight: 700;
            margin-bottom: 32px;
            padding-left: 8px;
            letter-spacing: 0.5px;
        }}
        .brand span {{
            color: #38bdf8;
        }}
        .menu-group {{
            display: flex;
            flex-direction: column;
            gap: 8px;
            flex-grow: 1;
        }}
        .menu-item {{
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 12px 14px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 14px;
            font-weight: 500;
            transition: all 0.2s ease;
            color: #94a3b8;
        }}
        .menu-item:hover {{
            background-color: rgba(255,255,255,0.05);
            color: #f1f5f9;
        }}
        .menu-item.active {{
            background: linear-gradient(90deg, #38bdf8 0%, #0284c7 100%);
            color: #ffffff;
            font-weight: 600;
            box-shadow: 0 4px 12px rgba(56, 189, 248, 0.2);
        }}
        .sidebar-footer {{
            border-top: 1px solid rgba(255,255,255,0.08);
            padding-top: 16px;
            display: flex;
            flex-direction: column;
            gap: 8px;
        }}
        .footer-btn {{
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 10px 12px;
            border-radius: 6px;
            font-size: 13px;
            cursor: pointer;
            transition: background 0.2s;
            color: #cbd5e1;
        }}
        .footer-btn:hover {{
            background-color: rgba(255,255,255,0.08);
        }}
        /* 右侧主内容区域 */
        .main-content {{
            flex-grow: 1;
            display: flex;
            flex-direction: column;
            height: 100%;
            background-color: #f8fafc;
        }}
        .header-bar {{
            height: 64px;
            background-color: #ffffff;
            border-bottom: 1px solid #e2e8f0;
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 0 32px;
        }}
        .header-title {{
            font-size: 16px;
            font-weight: 600;
            color: #0f172a;
        }}
        .user-profile {{
            display: flex;
            align-items: center;
            gap: 12px;
            font-size: 14px;
            color: #475569;
            font-weight: 500;
        }}
        .avatar {{
            width: 32px;
            height: 32px;
            border-radius: 50%;
            background: linear-gradient(135deg, #38bdf8 0%, #0284c7 100%);
            color: white;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            font-size: 13px;
        }}
        /* 工作台看板布局 */
        .dashboard-view {{
            padding: 32px;
            overflow-y: auto;
            flex-grow: 1;
            display: flex;
            flex-direction: column;
            gap: 24px;
        }}
        .welcome-card {{
            background: linear-gradient(135deg, #0284c7 0%, #0369a1 100%);
            border-radius: 16px;
            padding: 28px 32px;
            color: white;
            box-shadow: 0 10px 25px -5px rgba(2, 132, 199, 0.15);
        }}
        .welcome-card h2 {{
            margin: 0 0 8px 0;
            font-size: 24px;
            font-weight: 700;
        }}
        .welcome-card p {{
            margin: 0;
            font-size: 14px;
            color: #e0f2fe;
            opacity: 0.9;
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 20px;
        }}
        .stat-card {{
            background-color: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 12px;
            padding: 20px;
            display: flex;
            align-items: center;
            gap: 16px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.02);
        }}
        .stat-icon {{
            width: 48px;
            height: 48px;
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 22px;
        }}
        .stat-info {{
            display: flex;
            flex-direction: column;
        }}
        .stat-value {{
            font-size: 20px;
            font-weight: 700;
            color: #0f172a;
        }}
        .stat-label {{
            font-size: 12px;
            color: #64748b;
            margin-top: 2px;
            font-weight: 500;
        }}
        /* 核心特色功能卡片区 */
        .features-section {{
            display: flex;
            flex-direction: column;
            gap: 14px;
        }}
        .section-title {{
            font-size: 15px;
            font-weight: 700;
            color: #334155;
            letter-spacing: 0.3px;
        }}
        .features-grid {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 20px;
        }}
        .feature-card {{
            background-color: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 14px;
            padding: 24px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            gap: 16px;
            transition: all 0.2s ease;
            cursor: pointer;
            box-shadow: 0 1px 3px rgba(0,0,0,0.02);
        }}
        .feature-card:hover {{
            transform: translateY(-2px);
            box-shadow: 0 12px 20px -8px rgba(0,0,0,0.05);
            border-color: #cbd5e1;
        }}
        .feature-main {{
            display: flex;
            gap: 16px;
        }}
        .feature-badge {{
            width: 44px;
            height: 44px;
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 20px;
            flex-shrink: 0;
        }}
        .feature-text h3 {{
            margin: 0 0 4px 0;
            font-size: 15px;
            font-weight: 600;
            color: #0f172a;
        }}
        .feature-text p {{
            margin: 0;
            font-size: 13px;
            color: #64748b;
            line-height: 1.5;
        }}
        .feature-action {{
            align-self: flex-end;
            font-size: 12px;
            font-weight: 600;
            color: #0284c7;
            display: flex;
            align-items: center;
            gap: 4px;
        }}
        /* 通用现代化高级弹窗样式 */
        .modal-overlay {{
            position: fixed;
            top: 0;
            left: 0;
            width: 100vw;
            height: 100vh;
            background-color: rgba(15, 23, 42, 0.4);
            backdrop-filter: blur(4px);
            z-index: 1000;
            display: flex;
            align-items: center;
            justify-content: center;
            opacity: 0;
            pointer-events: none;
            transition: opacity 0.25s ease;
        }}
        .modal-overlay.active {{
            opacity: 1;
            pointer-events: auto;
        }}
        .modal-box {{
            background-color: #ffffff;
            border-radius: 16px;
            width: 440px;
            max-width: 90%;
            box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.15);
            transform: scale(0.95);
            transition: transform 0.25s ease;
            overflow: hidden;
        }}
        .modal-overlay.active .modal-box {{
            transform: scale(1);
        }}
        .modal-header {{
            padding: 20px 24px;
            border-bottom: 1px solid #f1f5f9;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }}
        .modal-title {{
            font-size: 16px;
            font-weight: 700;
            color: #0f172a;
        }}
        .modal-close {{
            font-size: 20px;
            color: #94a3b8;
            cursor: pointer;
            transition: color 0.2s;
            line-height: 1;
        }}
        .modal-close:hover {{
            color: #475569;
        }}
        .modal-body {{
            padding: 24px;
        }}
        .modal-footer {{
            padding: 16px 24px;
            border-top: 1px solid #f1f5f9;
            background-color: #f8fafc;
            display: flex;
            justify-content: flex-end;
        }}
        .modal-btn {{
            padding: 9px 20px;
            background: linear-gradient(135deg, #0284c7 0%, #0369a1 100%);
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 13px;
            font-weight: 600;
            cursor: pointer;
            box-shadow: 0 2px 4px rgba(2, 132, 199, 0.1);
        }}
        .modal-btn:hover {{
            opacity: 0.95;
        }}
    </style>
</head>
<body>

    <div class="app-container">
        <div class="sidebar">
            <div class="menu-group">
                <div class="brand">
                    <span>⚡</span> IELTS AI Pro
                </div>
                <div class="menu-item active" onclick="switchView('dashboard')">
                    🧭 <span>核心工作台</span>
                </div>
                <div class="menu-item" onclick="openPromoModal('🎁 专属学员福利群', '<div style=\'text-align:center; padding:10px 0; font-size:14px; color:#334155; line-height:1.6;\'>扫描下方二维码，加入雅思真题高频交流群：<br><br><b style=\'color:#2563eb; font-size:16px;\'>[ 模拟二维码占位符 ]</b><br><br>群内定期发放 2026 最新口语题库与高分范文。</div>')">
                    👥 <span>备考福利群</span>
                </div>
                <div class="menu-item" onclick="openSettingsModal()">
                    ⚙️ <span>系统偏好配置</span>
                </div>
            </div>
            
            <div class="sidebar-footer">
                <div class="footer-btn" onclick="openSystemNotice()">
                    📢 <span>系统更新公告</span>
                </div>
                <div class="footer-btn" style="color:#ef4444;" onclick="alert('安全退出成功！')">
                    🚪 <span>退出登录</span>
                </div>
            </div>
        </div>

        <div class="main-content">
            <div class="header-bar">
                <div class="header-title" id="current-view-title">雅思全能 AI 评测系统后台</div>
                <div class="user-profile">
                    <span>VIP 学员账号</span>
                    <div class="avatar">I</div>
                </div>
            </div>

            <div class="dashboard-view" id="dashboard-view">
                <div class="welcome-card">
                    <h2>欢迎来到雅思 AI 智能备考空间 ✨</h2>
                    <p>基于最新学术语言大模型深度调优，为您提供全网最严苛、最精准的雅思口语与写作全维度提分诊断。</p>
                </div>

                <div class="stats-grid">
                    <div class="stat-card">
                        <div class="stat-icon" style="background-color:#e0f2fe; color:#0369a1;">✍️</div>
                        <div class="stat-info">
                            <div class="stat-value">1,420 篇</div>
                            <div class="stat-label">全网今日批改</div>
                        </div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-icon" style="background-color:#dcfce7; color:#15803d;">🗣️</div>
                        <div class="stat-info">
                            <div class="stat-value">3,140 次</div>
                            <div class="stat-label">全网今日对练</div>
                        </div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-icon" style="background-color:#fef9c3; color:#a16207;">⚡</div>
                        <div class="stat-info">
                            <div class="stat-value">3.4 秒</div>
                            <div class="stat-label">AI 平均响应</div>
                        </div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-icon" style="background-color:#fee2e2; color:#b91c1c;">🎯</div>
                        <div class="stat-info">
                            <div class="stat-value">+1.5 分</div>
                            <div class="stat-label">学员平均跃升</div>
                        </div>
                    </div>
                </div>

                <div class="features-section">
                    <div class="section-title">🚀 雅思全科目 AI 智能评测矩阵</div>
                    <div class="features-grid">
                        <div class="feature-card" onclick="alert('正在为您接入：雅思 AI 写作全维批改引擎...')">
                            <div class="feature-main">
                                <div class="feature-badge" style="background-color: #eff6ff; color: #1d4ed8;">📝</div>
                                <div class="feature-text">
                                    <h3>雅思 AI 写作全维精细化批改</h3>
                                    <p>上传大小作文，AI 将严格按照官方审题、连贯衔接、词汇、语法四大维度深度解构，提供修改范文。</p>
                                </div>
                            </div>
                            <div class="feature-action">立即开始评测 →</div>
                        </div>

                        <div class="feature-card" onclick="alert('正在为您接入：雅思 AI 口语 1:1 模考私教...')">
                            <div class="feature-main">
                                <div class="feature-badge" style="background-color: #ecfdf5; color: #047857;">🎙️</div>
                                <div class="feature-text">
                                    <h3>雅思 AI 口语 1:1 沉浸式真题对练</h3>
                                    <p>支持真实真人发音对话，高维复刻 Part 1/2/3 全流程考场压力，实时生成详尽的地道表达建议报告。</p>
                                </div>
                            </div>
                            <div class="feature-action">开启真人对练 →</div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <div class="modal-overlay" id="global-modal">
        <div class="modal-box">
            <div class="modal-header">
                <div class="modal-title" id="modal-title">提示</div>
                <div class="modal-close" onclick="closePromoModal()">&times;</div>
            </div>
            <div class="modal-body" id="modal-body">
                内容加载中...
            </div>
            <div class="modal-footer">
                <button class="modal-btn" onclick="closePromoModal()">我知道了</button>
            </div>
        </div>
    </div>

    <script>
        function switchView(viewName) {{
            console.log('切换至视图:', viewName);
        }}

        function openPromoModal(title, contentHTML) {{
            document.getElementById('modal-title').innerText = title;
            document.getElementById('modal-body').innerHTML = contentHTML;
            document.getElementById('global-modal').classList.add('active');
        }}

        function closePromoModal() {{
            document.getElementById('global-modal').classList.remove('active');
        }}

        // 完美修复：系统偏好设置配置区排版样式
        function openSettingsModal() {{
            openPromoModal('⚙️ 系统偏好配置 (Settings)', `
                <div style="text-align:left; display:flex; flex-direction:column; gap:16px; color:#334155;">
                    
                    <div style="display:flex; flex-direction:column; gap:6px;">
                        <label style="font-weight:600; font-size:13px; color:#64748b; letter-spacing: 0.5px;">🚀 评测大模型引擎</label>
                        <select style="width:100%; padding:8px 12px; font-size:13px; font-family:inherit; color:#1e293b; border:1px solid #cbd5e1; border-radius:6px; background-color:#f8fafc; outline:none; cursor:pointer;">
                            <option>DeepSeek-V3 (极速高智商)</option>
                            <option>DeepSeek-R1 (深度长思考)</option>
                        </select>
                    </div>
                    
                    <div style="display:flex; flex-direction:column; gap:6px;">
                        <label style="font-weight:600; font-size:13px; color:#64748b; letter-spacing: 0.5px;">🎯 目标冲刺分数</label>
                        <select style="width:100%; padding:8px 12px; font-size:13px; font-family:inherit; color:#1e293b; border:1px solid #cbd5e1; border-radius:6px; background-color:#f8fafc; outline:none; cursor:pointer;">
                            <option>7.0 分冲刺营 (全面进阶)</option>
                            <option>7.5+ 分高分榜 (名校学术圈)</option>
                        </select>
                    </div>

                </div>
            `);
        }}

        // 完美修复：系统更新栏，规整中英文格式与段落行高
        function openSystemNotice() {{
            openPromoModal('📢 系统公告与版本更新', `
                <div style="text-align:left; display:flex; flex-direction:column; gap:12px; font-size:13px; line-height:1.6; color:#334155;">
                    <p style="border-bottom:1px solid #e2e8f0; padding-bottom:8px; margin:0;">
                        <span style="color:#2563eb; font-weight:bold;">🆕 系统更新 (2026年5月30日):</span><br>
                        <span style="font-weight:600; color:#0f172a;">DeepSeek-V3</span> 推理加速通道深度优化完毕，单次测评速度已缩短至 <span style="font-weight:600; color:#10b981;">3-5</span> 秒左右。
                    </p>
                    <p style="margin:0;">
                        <span style="color:#e11d48; font-weight:bold;">📅 考情公告:</span><br>
                        2026年 6 月雅思大作文官方机经预测与口语高频新题题库已更新至群文件中，点击左下角福利群加入获取。
                    </p>
                </div>
            `);
        }}
    </script>
</body>
</html>
"""

# 4. 将高阶单页 UI 直接通过 HTML 组件渲染展示
st.components.v1.html(html_code, height=1000, scrolling=False)
