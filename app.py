import streamlit as st
import json
from openai import OpenAI

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
MODEL_NAME = st.secrets.get("LLM_MODEL_NAME", "deepseek-chat")

# 初始化 session 状态（用于页面热重载与数据中转）
if "ai_output" not in st.session_state:
    st.session_state.ai_output = None
if "loading" not in st.session_state:
    st.session_state.loading = False
if "last_essay" not in st.session_state:
    st.session_state.last_essay = ""
if "last_prompt" not in st.session_state:
    st.session_state.last_prompt = ""
if "last_task" not in st.session_state:
    st.session_state.last_task = "IELTS Academic Task 2 (Essay)"

# 3. 稳健的 JSON 清洗函数，防止 API 返回 Markdown 格式标记
def clean_json_string(raw_str):
    s = raw_str.strip()
    tb = chr(96) * 3  # 动态生成 ```，防止 Python 解析歧义
    if s.startswith(tb):
        lines = s.split("\n")
        if len(lines) > 1:
            lines = lines[1:]
        if lines and lines[-1].strip() == tb:
            lines = lines[:-1]
        elif lines and lines[-1].endswith(tb):
            lines[-1] = lines[-1][:-3]
        s = "\n".join(lines)
    s = s.strip()
    if s.lower().startswith("json"):
        s = s[4:].strip()
    return s.strip()

# 4. 监听来自 iframe 中前端的“开始精批”URL 回传信号
query_params = st.query_params
if "essay" in query_params:
    essay_val = query_params["essay"]
    prompt_val = query_params.get("prompt", "")
    task_val = query_params.get("task", "IELTS Academic Task 2 (Essay)")
    
    # 存入 session 状态，用于数据回显和接口触发
    st.session_state.last_essay = essay_val
    st.session_state.last_prompt = prompt_val
    st.session_state.last_task = task_val
    st.session_state.loading = True
    
    # 清空 URL 参数，防止用户刷新网页时重复扣费请求 API
    st.query_params.clear()
    
    # 5. 调用 DeepSeek 大模型，强制其输出结构极其严密的诊断 JSON
    try:
        client = OpenAI(api_key=API_KEY, base_url=BASE_URL)
        SYSTEM_PROMPT = """You are an official senior IELTS Writing Examiner with 15+ years of experience.
Analyze the user's essay strictly based on official IELTS criteria. 
You MUST output ONLY a valid JSON object. Do not include markdown blocks like ```json or ```. 

JSON structure required:
{
  "overall": "例如 7.5",
  "level": "例如 Good User (C1 Advanced)",
  "tr": "得分",
  "cc": "得分",
  "lr": "得分",
  "gra": "得分",
  "strength_1": "中文描述第一个优势亮点...",
  "strength_2": "中文描述第二个优势亮点...",
  "improvement_1": "中文描述第1个改进建议...",
  "improvement_2": "中文描述第2个改进建议...",
  "refinement": "生成一篇 7.5+ 分水平的满分改写升级版范文...",
  "vocab_origin": "学生原作文中的差词",
  "vocab_boost": "升级后的高级词汇",
  "grammar_origin": "学生原作文中的语法错误",
  "grammar_fix": "纠正后的正确语法"
}"""
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"【Task Type】: {task_val}\n【Prompt】: {prompt_val}\n【Student Essay】: {essay_val}"}
            ],
            temperature=0.2
        )
        
        raw_content = response.choices[0].message.content
        clean_raw = clean_json_string(raw_content)
        st.session_state.ai_output = json.loads(clean_raw)
    except Exception as e:
        st.session_state.ai_output = {"error": f"Error during evaluation: {str(e)}"}
        
    st.session_state.loading = False
    st.rerun()

# 6. 安全转义 Python 状态，无缝灌入 JavaScript 环境中
js_ai_output = json.dumps(st.session_state.ai_output)
js_last_essay = json.dumps(st.session_state.last_essay)
js_last_prompt = json.dumps(st.session_state.last_prompt)
js_last_task = json.dumps(st.session_state.last_task)
js_loading_status = "true" if st.session_state.loading else "false"
js_api_configured = "true" if (API_KEY and "填写你的" not in API_KEY) else "false"

# 7. 纯本地高定 CSS 模板，彻底干掉外网 CDN
HTML_TEMPLATE = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8"/>
    <meta content="width=device-width, initial-scale=1.0" name="viewport"/>
    <title>IELTS AI Examiner Pro - Dashboard</title>
    
    <!-- 纯本地核心高定样式表，即使断网也能 100% 完美呈现 -->
    <style>
        :root {{
            --primary: #00236f;
            --secondary: #0051d5;
            --background: #f8f9ff;
            --surface: #ffffff;
            --surface-container-low: #eff4ff;
            --surface-container-high: #dce9ff;
            --text-primary: #0b1c30;
            --text-secondary: #444651;
            --border-color: #cbd5e1;
            --error: #ba1a1a;
            --success: #166534;
        }}

        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }}

        body {{
            font-family: 'Inter', -apple-system, "Segoe UI", Roboto, sans-serif;
            background-color: var(--background);
            color: var(--text-primary);
            height: 100vh;
            overflow: hidden;
            display: flex;
        }}

        /* 1. Left Sidebar Navigation */
        aside {{
            width: 280px;
            background-color: var(--surface-container-low);
            padding: 24px;
            border-right: 1px solid #e2e8f0;
            display: flex;
            flex-direction: column;
            height: 100%;
            position: fixed;
            left: 0;
            top: 0;
            z-index: 50;
        }}

        .brand-section {{
            margin-bottom: 32px;
        }}

        .brand-title {{
            font-size: 20px;
            font-weight: 900;
            color: var(--primary);
            display: flex;
            align-items: center;
            gap: 6px;
        }}

        .brand-sub {{
            font-size: 10px;
            font-weight: 800;
            color: var(--text-secondary);
            text-transform: uppercase;
            letter-spacing: 1.5px;
            margin-top: 4px;
            opacity: 0.7;
        }}

        nav {{
            display: flex;
            flex-direction: column;
            gap: 8px;
            flex-1;
        }}

        .nav-link {{
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 12px 16px;
            border-radius: 8px;
            text-decoration: none;
            color: var(--text-secondary);
            font-weight: 500;
            font-size: 14px;
            transition: all 0.2s;
        }}

        .nav-link:hover {{
            background-color: #e5eeff;
            color: var(--primary);
        }}

        .nav-link.active {{
            color: var(--primary);
            font-weight: 700;
            background-color: var(--surface-container-high);
            border-right: 4px solid var(--primary);
        }}

        .sidebar-footer {{
            margin-top: auto;
            display: flex;
            flex-direction: column;
            gap: 12px;
        }}

        .promo-card {{
            padding: 14px;
            border-radius: 12px;
            border: 1px solid #cbd5e1;
            box-shadow: 0 4px 6px -1px rgba(30, 58, 138, 0.03);
        }}

        .promo-card.blue {{
            background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
            border-color: #bfdbfe;
        }}

        .promo-card.indigo {{
            background: linear-gradient(135deg, #f5f3ff 0%, #edd8ff 100%);
            border-color: #ddd6fe;
        }}

        .promo-header {{
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 12px;
            font-weight: 800;
            color: var(--primary);
            margin-bottom: 6px;
        }}

        .promo-text {{
            font-size: 11px;
            line-height: 1.5;
            color: #1e3a8a;
        }}

        .sidebar-bottom-row {{
            border-top: 1px solid #cbd5e1;
            padding-top: 12px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 10px;
            font-weight: bold;
            color: var(--text-secondary);
        }}

        /* 2. Top AppBar Shell */
        header {{
            height: 64px;
            border-bottom: 1px solid #cbd5e1;
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 0 32px;
            position: fixed;
            left: 280px;
            right: 0;
            top: 0;
            background: var(--surface);
            z-index: 40;
        }}

        .header-title-group {{
            display: flex;
            align-items: center;
            gap: 32px;
        }}

        .header-brand-name {{
            font-size: 18px;
            font-weight: 900;
            color: var(--primary);
            letter-spacing: -0.5px;
        }}

        .header-tabs {{
            display: flex;
            gap: 16px;
        }}

        .header-tab-item {{
            font-size: 12px;
            font-weight: 700;
            cursor: pointer;
            color: var(--text-secondary);
            padding-bottom: 4px;
            transition: all 0.2s;
        }}

        .header-tab-item:hover, .header-tab-item.active {{
            color: var(--primary);
            border-bottom: 2px solid var(--primary);
        }}

        .header-right {{
            display: flex;
            align-items: center;
            gap: 16px;
        }}

        .new-btn {{
            background: var(--primary);
            color: #fff;
            border: none;
            padding: 8px 16px;
            border-radius: 8px;
            font-size: 12px;
            font-weight: 700;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 6px;
            transition: all 0.2s;
        }}

        .new-btn:hover {{
            opacity: 0.9;
            transform: scale(1.02);
        }}

        .avatar {{
            width: 32px;
            height: 32px;
            border-radius: 50%;
            overflow: hidden;
            border: 1px solid #cbd5e1;
        }}

        .avatar img {{
            width: 100%;
            height: 100%;
            object-fit: cover;
        }}

        /* 3. Main Layout Containers */
        main {{
            margin-left: 280px;
            margin-top: 64px;
            height: calc(100vh - 64px);
            display: flex;
            gap: 24px;
            padding: 24px;
            overflow: hidden;
            width: calc(100% - 280px);
        }}

        section {{
            display: flex;
            flex-direction: column;
            gap: 16px;
            height: 100%;
        }}

        section.left-panel {{
            width: 45%;
        }}

        section.right-panel {{
            flex: 1;
        }}

        .panel-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}

        .panel-title {{
            font-size: 16px;
            font-weight: 800;
            color: var(--primary);
            display: flex;
            align-items: center;
            gap: 8px;
        }}

        .panel-badge {{
            font-size: 10px;
            font-weight: 800;
            background-color: var(--surface-container-high);
            color: var(--primary);
            padding: 4px 8px;
            border-radius: 4px;
        }}

        /* Content Boxes */
        .content-box {{
            background: var(--surface);
            border: 1px solid #cbd5e1;
            border-radius: 16px;
            padding: 24px;
            box-shadow: 0 4px 6px -1px rgba(30, 58, 138, 0.02);
            flex: 1;
            display: flex;
            flex-direction: column;
            gap: 16px;
            overflow: hidden;
        }}

        .input-group {{
            display: flex;
            flex-direction: column;
            gap: 6px;
        }}

        .input-label {{
            font-size: 12px;
            font-weight: 700;
            color: var(--text-secondary);
        }}

        select, textarea {{
            width: 100%;
            border-radius: 8px;
            border: 1px solid #cbd5e1;
            padding: 10px 12px;
            font-size: 13px;
            color: var(--text-primary);
            outline: none;
            background-color: #fff;
            transition: all 0.2s;
        }}

        select:focus, textarea:focus {{
            border-color: var(--primary);
            box-shadow: 0 0 0 2px rgba(0, 35, 111, 0.1);
        }}

        textarea {{
            resize: none;
        }}

        .textarea-flex {{
            flex: 1;
            display: flex;
            flex-direction: column;
        }}

        .textarea-flex textarea {{
            flex: 1;
        }}

        .word-count {{
            display: flex;
            justify-content: flex-end;
            font-size: 11px;
            color: var(--text-secondary);
            font-weight: 600;
            margin-top: 4px;
        }}

        .cta-btn {{
            width: 100%;
            background: linear-gradient(90deg, var(--primary) 0%, var(--secondary) 100%);
            color: #fff;
            border: none;
            padding: 14px;
            border-radius: 12px;
            font-size: 15px;
            font-weight: 800;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
            box-shadow: 0 4px 10px rgba(0, 35, 111, 0.15);
            transition: all 0.2s;
        }}

        .cta-btn:hover {{
            transform: translateY(-1px);
            box-shadow: 0 6px 15px rgba(0, 35, 111, 0.2);
        }}

        .cta-btn:active {{
            transform: scale(0.98);
        }}

        /* 4. Output States Layout */
        .right-viewport {{
            flex: 1;
            position: relative;
            overflow: hidden;
            border-radius: 16px;
            height: 100%;
        }}

        /* Empty State */
        .empty-state {{
            position: absolute;
            inset: 0;
            background-color: var(--surface-container-low);
            border: 2px dashed #cbd5e1;
            border-radius: 16px;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            padding: 32px;
            text-align: center;
            gap: 16px;
        }}

        .empty-icon-circle {{
            width: 64px;
            height: 64px;
            border-radius: 50%;
            background-color: var(--surface-container-high);
            display: flex;
            align-items: center;
            justify-content: center;
            color: var(--primary);
        }}

        .empty-text-title {{
            font-size: 14px;
            font-weight: 800;
            color: var(--text-primary);
            margin-bottom: 6px;
        }}

        .empty-text-sub {{
            font-size: 12px;
            color: var(--text-secondary);
            line-height: 1.6;
            max-width: 320px;
        }}

        /* Loading State Overlay */
        .loading-overlay {{
            position: absolute;
            inset: 0;
            background-color: rgba(255, 255, 255, 0.9);
            backdrop-filter: blur(2px);
            z-index: 10;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            gap: 12px;
        }}

        .spinner {{
            width: 40px;
            height: 40px;
            border: 4px solid rgba(0, 35, 111, 0.1);
            border-top: 4px solid var(--primary);
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }}

        .loading-text {{
            font-weight: 800;
            font-size: 14px;
            color: var(--primary);
        }}

        .loading-sub {{
            font-size: 10px;
            color: var(--text-secondary);
            font-weight: bold;
        }}

        /* Real Result View Panel (Scrollable) */
        .result-scroll-wrapper {{
            position: absolute;
            inset: 0;
            overflow-y: auto;
            display: flex;
            flex-direction: column;
            gap: 16px;
            padding-right: 4px;
        }}

        .result-scroll-wrapper::-webkit-scrollbar {{
            width: 6px;
        }}

        .result-scroll-wrapper::-webkit-scrollbar-thumb {{
            background-color: #cbd5e1;
            border-radius: 20px;
        }}

        /* Band Score Hero Card */
        .score-hero-card {{
            background: #fff;
            border: 1px solid #cbd5e1;
            border-radius: 12px;
            padding: 24px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            box-shadow: 0 4px 6px -1px rgba(30, 58, 138, 0.03);
        }}

        .score-label {{
            font-size: 10px;
            font-weight: 900;
            color: #94a3b8;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}

        .score-big-num {{
            font-size: 48px;
            font-weight: 900;
            color: var(--primary);
            line-height: 1.1;
        }}

        .score-level-desc {{
            font-size: 12px;
            color: var(--secondary);
            font-weight: 800;
            margin-top: 4px;
        }}

        .sub-scores-grid {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 8px;
        }}

        .sub-score-box {{
            background-color: var(--background);
            border: 1px solid #f1f5f9;
            padding: 8px 12px;
            border-radius: 8px;
            text-align: center;
            min-width: 60px;
        }}

        .sub-score-box .name {{
            font-size: 9px;
            color: #94a3b8;
            font-weight: 900;
        }}

        .sub-score-box .val {{
            font-size: 16px;
            font-weight: 800;
            color: var(--primary);
            margin-top: 2px;
        }}

        /* Bento Grid: Strengths & Weaknesses */
        .bento-grid {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 16px;
        }}

        .bento-card {{
            background: #fff;
            border: 1px solid #cbd5e1;
            border-radius: 12px;
            padding: 16px;
            box-shadow: 0 4px 6px -1px rgba(30, 58, 138, 0.03);
            border-left-width: 4px;
        }}

        .bento-card.success {{
            border-left-color: var(--secondary);
        }}

        .bento-card.error {{
            border-left-color: var(--error);
        }}

        .bento-card-title {{
            font-size: 12px;
            font-weight: 800;
            display: flex;
            align-items: center;
            gap: 6px;
            margin-bottom: 12px;
        }}

        .bento-card-title.success {{ color: var(--secondary); }}
        .bento-card-title.error {{ color: var(--error); }}

        .bento-list {{
            list-style: none;
            display: flex;
            flex-direction: column;
            gap: 8px;
            font-size: 12px;
            color: var(--text-secondary);
            line-height: 1.5;
        }}

        /* AI Refinement Card */
        .refinement-card {{
            background: #fff;
            border: 1px solid #cbd5e1;
            border-radius: 12px;
            padding: 24px;
            box-shadow: 0 4px 6px -1px rgba(30, 58, 138, 0.03);
        }}

        .refinement-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 12px;
        }}

        .refinement-title {{
            font-size: 13px;
            font-weight: 800;
            color: var(--primary);
        }}

        .copy-btn {{
            border: none;
            background: none;
            color: var(--primary);
            font-size: 11px;
            font-weight: 700;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 4px;
        }}

        .copy-btn:hover {{
            text-decoration: underline;
        }}

        .refinement-body {{
            background-color: var(--background);
            border: 1px solid #f1f5f9;
            padding: 16px;
            border-radius: 8px;
            font-size: 12px;
            font-style: italic;
            color: #475569;
            line-height: 1.6;
            word-break: break-word;
        }}

        .refinement-grid {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 16px;
            margin-top: 16px;
        }}

        .boost-box {{
            background-color: var(--background);
            border: 1px solid #f1f5f9;
            padding: 12px;
            border-radius: 8px;
        }}

        .boost-tag {{
            font-size: 9px;
            color: #94a3b8;
            font-weight: 900;
            text-transform: uppercase;
        }}

        .boost-content {{
            font-size: 12px;
            margin-top: 4px;
            line-height: 1.4;
        }}

        /* Animations */
        @keyframes spin {{
            0% {{ transform: rotate(0deg); }}
            100% {{ transform: rotate(360deg); }}
        }}

        /* Material Icons fallback standard mapping */
        .icon-symbol {{
            font-family: 'Material Symbols Outlined';
            font-weight: normal;
            font-style: normal;
            font-size: 20px;
            line-height: 1;
            letter-spacing: normal;
            text-transform: none;
            display: inline-block;
            white-space: nowrap;
            word-wrap: normal;
            direction: ltr;
            -webkit-font-feature-settings: 'liga';
            -webkit-font-smoothing: antialiased;
        }}
    </style>
</head>
<body>

    <!-- 1. Left Sidebar Navigation -->
    <aside>
        <div class="brand-section">
            <h1 class="brand-title">🎓 雅思AI备考中心</h1>
            <p class="brand-sub">Premium v2.5</p>
        </div>
        <nav>
            <a class="nav-link active" href="#" id="nav-dash">
                <span class="icon-symbol">dashboard</span>
                <span>Dashboard</span>
            </a>
            <a class="nav-link" href="#" id="nav-history">
                <span class="icon-symbol">history</span>
                <span>Essay History</span>
            </a>
            <a class="nav-link" href="#" id="nav-groups">
                <span class="icon-symbol">group</span>
                <span>Study Groups</span>
            </a>
            <a class="nav-link" href="#" id="nav-pro">
                <span class="icon-symbol">workspace_premium</span>
                <span>Pro Benefits</span>
            </a>
        </nav>
        
        <div class="sidebar-footer">
            <div class="promo-card blue">
                <div class="promo-header">
                    <span class="icon-symbol" style="font-variation-settings: 'FILL' 1">card_giftcard</span>
                    <span>🎁 独家备考福利</span>
                </div>
                <p class="promo-text">后台回复 “<b>雅思真题</b>” 即可免费领取 2026 最新雅思考试机经预测及高分词汇表。</p>
            </div>
            
            <div class="promo-card indigo">
                <div class="promo-header">
                    <span class="icon-symbol" style="font-variation-settings: 'FILL' 1">groups</span>
                    <span>👥 互助打卡群</span>
                </div>
                <p class="promo-text">添加学长微信，备注 “<b>作文打卡</b>”，受邀加入千人雅思备考群。</p>
            </div>
            
            <div class="sidebar-bottom-row">
                <span>⚙️ DeepSeek-V3 Support</span>
                <span class="icon-symbol" style="font-size:16px; cursor:pointer;">help_outline</span>
            </div>
        </div>
    </aside>

    <!-- 2. Top AppBar -->
    <header>
        <div class="header-title-group">
            <span class="header-brand-name">IELTS AI Examiner Pro</span>
            <div class="header-tabs">
                <span class="header-tab-item active">TR</span>
                <span class="header-tab-item">CC</span>
                <span class="header-tab-item">LR</span>
                <span class="header-tab-item">GRA</span>
            </div>
        </div>
        <div class="header-right">
            <button onclick="resetTest()" class="new-btn">
                <span class="icon-symbol" style="font-size:16px;">add</span>
                New Analysis
            </button>
            <span class="icon-symbol" style="color:#757682; cursor:pointer;">notifications</span>
            <span class="icon-symbol" style="color:#757682; cursor:pointer;">settings</span>
            <div class="avatar">
                <img alt="User Avatar" src="[https://lh3.googleusercontent.com/aida-public/AB6AXuA6OsXNWZ68DPQHc81CV6O6_nnxwGSPx2rK82Km0XDB5dMrJIdt6eewicggxVE44SPbbqDv-QJnxSB8yYSfOXC0-DcoETi4yO9e2S_wGGwqVaMlQJd8TkRncoVcFw3Fi9JzmWlNujI6mHKhmOx4MoDrLLAngvmaW-5dZD1lZTxYLsXeu_IK6Lq-0gd4YmvT2YxSTk35vkiqcyZLXI8CI9WmkaysWRl_uFesTx6vL9RSwEteK5Esa63RaMTi884rqIlfnbzFn216jg](https://lh3.googleusercontent.com/aida-public/AB6AXuA6OsXNWZ68DPQHc81CV6O6_nnxwGSPx2rK82Km0XDB5dMrJIdt6eewicggxVE44SPbbqDv-QJnxSB8yYSfOXC0-DcoETi4yO9e2S_wGGwqVaMlQJd8TkRncoVcFw3Fi9JzmWlNujI6mHKhmOx4MoDrLLAngvmaW-5dZD1lZTxYLsXeu_IK6Lq-0gd4YmvT2YxSTk35vkiqcyZLXI8CI9WmkaysWRl_uFesTx6vL9RSwEteK5Esa63RaMTi884rqIlfnbzFn216jg)"/>
            </div>
        </div>
    </header>

    <!-- 3. Main Body Canvas -->
    <main>
        <!-- Left Panel: Form Submission -->
        <section class="left-panel">
            <div class="panel-header">
                <h2 class="panel-title">
                    <span class="icon-symbol" style="color:var(--primary);">edit_note</span>
                    📥 提交作文本系统
                </h2>
                <span class="panel-badge">Academic Mode</span>
            </div>
            
            <div class="content-box">
                <div class="input-group">
                    <label class="input-label">📝 选择你的作文类型 (Task Type)</label>
                    <select id="taskSelect">
                        <option value="IELTS Academic Task 2 (Essay)">IELTS Academic Task 2 (Essay)</option>
                        <option value="IELTS Academic Task 1 (Report/Data)">IELTS Academic Task 1 (Report/Data)</option>
                        <option value="IELTS General Training Task 1 (Letter)">IELTS General Training Task 1 (Letter)</option>
                    </select>
                </div>
                
                <div class="input-group">
                    <label class="input-label">📌 输入作文题目 (Prompt/Question)</label>
                    <textarea id="promptInput" rows="3" placeholder="Type or paste the exam question here..."></textarea>
                </div>
                
                <div class="input-group textarea-flex">
                    <label class="input-label">✍️ 粘贴你的文章 (Your Essay)</label>
                    <textarea id="essayInput" oninput="updateWordCount()" placeholder="Start writing or paste your essay content here. Minimum 250 words recommended for Task 2..."></textarea>
                    <div class="word-count">
                        <span id="wordCount">Word Count: 0 words</span>
                    </div>
                </div>
                
                <button onclick="startAnalysis()" class="cta-btn" id="startAnalysisBtn">
                    <span class="icon-symbol" style="color:#fff;">rocket_launch</span>
                    🚀 开始 AI 深度精批
                </button>
            </div>
        </section>

        <!-- Right Panel: Diagnostics Outputs -->
        <section class="right-panel">
            <div class="panel-header">
                <h2 class="panel-title">
                    <span class="icon-symbol" style="color:var(--primary);">analytics</span>
                    📊 AI 评估结果报告
                </h2>
            </div>
            
            <div class="right-viewport">
                <!-- 1. Default State (Empty Dashboard) -->
                <div class="empty-state" id="emptyState">
                    <div class="empty-icon-circle">
                        <span class="icon-symbol" style="font-size:36px;">psychology</span>
                    </div>
                    <div>
                        <h3 class="empty-text-title">等待评估</h3>
                        <p class="empty-text-sub">💡 在左侧填写好题目和作文，点击“开始 AI 深度精批”，5秒内为您呈献满分改写与四维诊断报告。</p>
                    </div>
                </div>

                <!-- 2. Loading Spinner Page -->
                <div class="loading-overlay" id="loadingOverlay" style="display:none;">
                    <div class="spinner"></div>
                    <p class="loading-text">DeepSeek-V3 正在深度分析评测中...</p>
                    <p class="loading-sub">预计等待时间: 3秒</p>
                </div>

                <!-- 3. Real Result Panel (Initially Hidden) -->
                <div class="result-scroll-wrapper" id="analysisResult" style="display:none;">
                    <!-- Band Score Hero Header -->
                    <div class="score-hero-card">
                        <div>
                            <p class="score-label">Overall Band Score</p>
                            <h3 class="score-big-num" id="resOverall">7.5</h3>
                            <p class="score-level-desc" id="resLevel">Good User (C1 Advanced)</p>
                        </div>
                        <div class="sub-scores-grid">
                            <div class="sub-score-box">
                                <p class="name">TR</p>
                                <p class="val" id="resTR">7.0</p>
                            </div>
                            <div class="sub-score-box">
                                <p class="name">CC</p>
                                <p class="val" id="resCC">7.5</p>
                            </div>
                            <div class="sub-score-box">
                                <p class="name">LR</p>
                                <p class="val" id="resLR">8.0</p>
                            </div>
                            <div class="sub-score-box">
                                <p class="name">GRA</p>
                                <p class="val" id="resGRA">7.0</p>
                            </div>
                        </div>
                    </div>

                    <!-- Strengths and Improvements Bento -->
                    <div class="bento-grid">
                        <div class="bento-card success">
                            <div class="bento-card-title success">
                                <span class="icon-symbol" style="font-variation-settings: 'FILL' 1">verified</span>
                                <span>优势亮点 (Strengths)</span>
                            </div>
                            <ul class="bento-list">
                                <li id="resS1">• 词汇丰富度极高，使用了学术化表达。</li>
                                <li id="resS2">• 论点逻辑清晰。</li>
                            </ul>
                        </div>
                        
                        <div class="bento-card error">
                            <div class="bento-card-title error">
                                <span class="icon-symbol" style="font-variation-settings: 'FILL' 1">report</span>
                                <span>改进建议 (Areas for Improvement)</span>
                            </div>
                            <ul class="bento-list">
                                <li id="resI1">• 论证略显单薄。</li>
                                <li id="resI2">• 注意复合句中的标点符号。</li>
                            </ul>
                        </div>
                    </div>

                    <!-- AI Refinement Showcase Card -->
                    <div class="refinement-card">
                        <div class="refinement-header">
                            <h4 class="refinement-title">✨ AI 满分改写建议 (Refinement)</h4>
                            <button onclick="copyModelEssay()" class="copy-btn">
                                <span class="icon-symbol" style="font-size:14px;">content_copy</span>
                                <span>Copy Essay</span>
                            </button>
                        </div>
                        <div class="refinement-body" id="resRefinement">
                            Refining...
                        </div>
                        <div class="refinement-grid">
                            <div class="boost-box">
                                <p class="boost-tag">Vocabulary Boost</p>
                                <p class="boost-content" id="resVocab">Instead of "bad effect", use <span style="color:var(--secondary); font-weight:bold;">"detrimental impact"</span></p>
                            </div>
                            <div class="boost-box">
                                <p class="boost-tag">Grammar Fix</p>
                                <p class="boost-content" id="resGrammar">Correction: <span style="color:var(--error); text-decoration:line-through;">"The research show"</span> → <span style="color:var(--secondary); font-weight:bold;">"shows"</span></p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </section>
    </main>

    <!-- Global Decoration Watermark -->
    <div style="position:fixed; bottom:16px; right:16px; pointer-events:none; opacity:0.35;">
        <img alt="British Council" style="width:48px; height:48px; object-fit:contain;" src="[https://lh3.googleusercontent.com/aida-public/AB6AXuCq8sxODXxAXBxSUcisb44SNIFUxvaWJm6xgfNYJz5w6I0XGSgDdDF4sbHCo_HlVkGZfTFYaHzXLxVMLBXAUWObMerq-O2jZ-GuWQ-LQvXq-Ecy8KZl4FQRVkhlBp8hGUtBR_aIK7Uhn49GgSfGa_CnKLoqv45YLsqIsjbUiImF2w0pFYYCNsimc5d0IJrksk6s1BIcYMUgfXb_NinfTuVtf5Gl07AJ8pA3F-ehOnHE9bOeX2U8EaAhRWFBHJ1WUe4EukL0MBB63Q](https://lh3.googleusercontent.com/aida-public/AB6AXuCq8sxODXxAXBxSUcisb44SNIFUxvaWJm6xgfNYJz5w6I0XGSgDdDF4sbHCo_HlVkGZfTFYaHzXLxVMLBXAUWObMerq-O2jZ-GuWQ-LQvXq-Ecy8KZl4FQRVkhlBp8hGUtBR_aIK7Uhn49GgSfGa_CnKLoqv45YLsqIsjbUiImF2w0pFYYCNsimc5d0IJrksk6s1BIcYMUgfXb_NinfTuVtf5Gl07AJ8pA3F-ehOnHE9bOeX2U8EaAhRWFBHJ1WUe4EukL0MBB63Q)"/>
    </div>

    <!-- 4. Pure Frontend Controller JS Bridge -->
    <script>
        const aiOutput = {js_ai_output};
        const lastEssay = {js_last_essay};
        const lastPrompt = {js_last_prompt};
        const lastTask = {js_last_task};
        const stLoading = {js_loading_status};
        const apiConfigured = {js_api_configured};

        window.onload = function() {{
            // 恢复上一次在输入框填写的作文和题目
            if (lastEssay) document.getElementById('essayInput').value = lastEssay;
            if (lastPrompt) document.getElementById('promptInput').value = lastPrompt;
            if (lastTask) document.getElementById('taskSelect').value = lastTask;
            updateWordCount();

            // 根据状态切换视图显示
            if (stLoading) {{
                document.getElementById('loadingOverlay').style.display = 'flex';
                document.getElementById('emptyState').style.display = 'none';
                document.getElementById('analysisResult').style.display = 'none';
            }} else if (aiOutput) {{
                document.getElementById('loadingOverlay').style.display = 'none';
                document.getElementById('emptyState').style.display = 'none';
                
                if (aiOutput.error) {{
                    alert("接口请求发生错误: " + aiOutput.error);
                    document.getElementById('emptyState').style.display = 'flex';
                }} else {{
                    // 动态塞入真实 API 评测数据
                    document.getElementById('resOverall').innerText = aiOutput.overall || "5.5";
                    document.getElementById('resLevel').innerText = aiOutput.level || "Band Score";
                    document.getElementById('resTR').innerText = aiOutput.tr || "-";
                    document.getElementById('resCC').innerText = aiOutput.cc || "-";
                    document.getElementById('resLR').innerText = aiOutput.lr || "-";
                    document.getElementById('resGRA').innerText = aiOutput.gra || "-";
                    
                    document.getElementById('resS1').innerText = "• " + (aiOutput.strength_1 || "");
                    document.getElementById('resS2').innerText = "• " + (aiOutput.strength_2 || "");
                    
                    document.getElementById('resI1').innerHTML = `<span style="color:var(--error); font-weight:bold;">•</span> <span>${{aiOutput.improvement_1 || ""}}</span>`;
                    document.getElementById('resI2').innerHTML = `<span style="color:var(--error); font-weight:bold;">•</span> <span>${{aiOutput.improvement_2 || ""}}</span>`;
                    
                    document.getElementById('resRefinement').innerText = aiOutput.refinement || "";
                    
                    document.getElementById('resVocab').innerHTML = `Instead of "${{aiOutput.vocab_origin || "bad effect"}}", use <span style="color:var(--secondary); font-weight:bold;">"${{aiOutput.vocab_boost || "detrimental impact"}}"</span>`;
                    document.getElementById('resGrammar').innerHTML = `Correction: <span style="color:var(--error); text-decoration:line-through;">"${{aiOutput.grammar_origin || ""}}"</span> → <span style="color:var(--secondary); font-weight:bold;">"${{aiOutput.grammar_fix || ""}}"</span>`;
                    
                    document.getElementById('analysisResult').style.display = 'flex';
                }}
            }}
        }};

        // 点击按钮运行分析
        function startAnalysis() {{
            const essay = document.getElementById('essayInput').value.trim();
            const prompt = document.getElementById('promptInput').value.trim();
            const task = document.getElementById('taskSelect').value;

            if (!essay || !prompt) {{
                alert("⚠️ 请确保题目和文章内容都已填写完整！");
                return;
            }}

            if (!apiConfigured) {{
                alert("❌ 未配置 API Key，请先在 Streamlit 的 Settings -> Secrets 中贴入真实的 DeepSeek Key！");
                return;
            }}

            // 触发立即加载动画
            document.getElementById('loadingOverlay').style.display = 'flex';
            document.getElementById('emptyState').style.display = 'none';
            document.getElementById('analysisResult').style.display = 'none';

            // 通过 URL 回传向 Streamlit 触发 Rerun 任务并传递入参
            const targetUrl = window.parent.location.origin + window.parent.location.pathname + 
                "?task=" + encodeURIComponent(task) + 
                "&prompt=" + encodeURIComponent(prompt) + 
                "&essay=" + encodeURIComponent(essay);
            
            window.parent.location.href = targetUrl;
        }}

        // 清空输入和状态
        function resetTest() {{
            document.getElementById('essayInput').value = "";
            document.getElementById('promptInput').value = "";
            updateWordCount();
            window.parent.location.href = window.parent.location.origin + window.parent.location.pathname;
        }}

        // 单词计算器
        function updateWordCount() {{
            const text = document.getElementById('essayInput').value.trim();
            const count = text ? text.split(/\\s+/).length : 0;
            document.getElementById('wordCount').innerText = `Word Count: ${{count}} words`;
        }}

        // 复制高分文章
        function copyModelEssay() {{
            const text = document.getElementById('resRefinement').innerText;
            const temp = document.createElement("textarea");
            temp.value = text;
            document.body.appendChild(temp);
            temp.select();
            document.execCommand("copy");
            document.body.removeChild(temp);
            alert("📋 满分改写范文已成功复制到剪贴板！");
        }}
    </script>
</body>
</html>
"""

# 8. 全屏一键无缝注入
st.components.v1.html(HTML_TEMPLATE, height=720, scrolling=False)
