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

# 预置或初始化作文批改历史记录
if "essay_history" not in st.session_state:
    st.session_state.essay_history = [
        {
            "id": "mock_1",
            "date": "2026-05-29 14:20",
            "task": "IELTS Academic Task 2 (Essay)",
            "prompt": "Some people think that universities should provide knowledge and skills needed in the workplace. Others think the primary function should be to give access to knowledge.",
            "essay": "In my opinion, I am agree that university should teach skills for jobs. Nowadays, find a good job is very difficult for young people. If university only teach theory, students cannot get money after graduate.",
            "overall": "5.5",
            "level": "Competent User (B2 Basic)",
            "tr": "6.0",
            "cc": "5.5",
            "lr": "5.0",
            "gra": "5.0",
            "strength_1": "文章立场基本明确，能针对大学教育的双重目的开展议论。",
            "strength_2": "段落划分基本清晰，结尾给出了个人的总结性立场。",
            "improvement_1": "出现多处严重的动词主语和主谓一致错误（如 I am agree, find a good job is）。",
            "improvement_2": "词汇使用匮乏，且大量口语化表达（如 get money, after graduate）不符合学术规范。",
            "refinement": "While a camp of thinkers asserts that higher education institutions should primary act as a training ground for vocational readiness, others contend that universities ought to remain sanctuaries for academic enlightenment. In my perspective...",
            "vocab_origin": "get money",
            "vocab_boost": "earn a livelihood / secure financial independence",
            "grammar_origin": "I am agree that university should teach",
            "grammar_fix": "I agree that universities should teach"
        }
    ]

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
        parsed_result = json.loads(clean_raw)
        
        # 写入前端展示状态
        st.session_state.ai_output = parsed_result
        
        # 自动将此次分析成果追加至历史列表
        new_record = {
            "id": f"rec_{int(datetime.now().timestamp())}",
            "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "task": task_val,
            "prompt": prompt_val,
            "essay": essay_val,
            **parsed_result
        }
        st.session_state.essay_history.insert(0, new_record)
        
    except Exception as e:
        st.session_state.ai_output = {"error": f"Error during evaluation: {str(e)}"}
        
    st.session_state.loading = False
    st.rerun()

# 处理历史加载的回调信号
if "load_history_id" in query_params:
    target_id = query_params["load_history_id"]
    st.query_params.clear()
    # 查找对应记录并进行回装
    matched = next((item for item in st.session_state.essay_history if item["id"] == target_id), None)
    if matched:
        st.session_state.last_essay = matched["essay"]
        st.session_state.last_prompt = matched["prompt"]
        st.session_state.last_task = matched["task"]
        st.session_state.ai_output = {
            "overall": matched["overall"],
            "level": matched["level"],
            "tr": matched["tr"],
            "cc": matched["cc"],
            "lr": matched["lr"],
            "gra": matched["gra"],
            "strength_1": matched["strength_1"],
            "strength_2": matched["strength_2"],
            "improvement_1": matched["improvement_1"],
            "improvement_2": matched["improvement_2"],
            "refinement": matched["refinement"],
            "vocab_origin": matched["vocab_origin"],
            "vocab_boost": matched["vocab_boost"],
            "grammar_origin": matched["grammar_origin"],
            "grammar_fix": matched["grammar_fix"]
        }
        st.rerun()

# 6. 安全转义 Python 状态，无缝灌入 JavaScript 环境中
js_ai_output = json.dumps(st.session_state.ai_output)
js_last_essay = json.dumps(st.session_state.last_essay)
js_last_prompt = json.dumps(st.session_state.last_prompt)
js_last_task = json.dumps(st.session_state.last_task)
js_essay_history = json.dumps(st.session_state.essay_history)
js_loading_status = "true" if st.session_state.loading else "false"
js_api_configured = "true" if (API_KEY and "填写你的" not in API_KEY) else "false"

# 7. 纯本地高定 CSS 模板，修复 Google 考官专用图标和所有交互功能
HTML_TEMPLATE = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8"/>
    <meta content="width=device-width, initial-scale=1.0" name="viewport"/>
    <title>IELTS AI Examiner Pro - Dashboard</title>
    
    <!-- 1. 强力引入 Google 图标库，彻底解决图片中文字露白、扭曲的情况 -->
    <link href="[https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200](https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200)" rel="stylesheet" />
    
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

        /* Left Sidebar Navigation */
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
            flex-grow: 1;
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
            cursor: pointer;
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

        /* Top AppBar Shell */
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

        /* Top Bar Header Buttons */
        .icon-btn {{
            background: none;
            border: none;
            cursor: pointer;
            color: #757682;
            transition: color 0.2s;
            display: flex;
            align-items: center;
            justify-content: center;
        }}
        .icon-btn:hover {{
            color: var(--primary);
        }}

        /* Beautiful Custom SVG Academic Avatar placeholder */
        .academic-avatar-svg {{
            width: 34px;
            height: 34px;
            border-radius: 50%;
            border: 2px solid var(--primary);
            background: #eff4ff;
            cursor: pointer;
        }}

        /* Main View Shell */
        main {{
            margin-left: 280px;
            margin-top: 64px;
            height: calc(100vh - 64px);
            padding: 24px;
            overflow: hidden;
            width: calc(100% - 280px);
            position: relative;
        }}

        /* View blocks */
        .view-block {{
            display: none; /* Controlled by JS switcher */
            width: 100%;
            height: 100%;
            gap: 24px;
            overflow: hidden;
        }}
        .view-block.active {{
            display: flex;
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

        /* Output Viewport Area */
        .right-viewport {{
            flex: 1;
            position: relative;
            overflow: hidden;
            border-radius: 16px;
            height: 100%;
        }}

        /* Empty State default dashboard view */
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

        /* Spinner Loading Screen */
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

        /* Analysis Result Panel */
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

        /* ----------------------------------------------------- */
        /* TAB 2: Essay History View Styles */
        /* ----------------------------------------------------- */
        .history-full-view {{
            width: 100%;
            height: 100%;
            background: #fff;
            border: 1px solid #cbd5e1;
            border-radius: 16px;
            padding: 24px;
            display: flex;
            flex-direction: column;
            gap: 16px;
        }}

        .history-title-row {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid #e2e8f0;
            padding-bottom: 12px;
        }}

        .history-scroll-container {{
            flex: 1;
            overflow-y: auto;
            display: flex;
            flex-direction: column;
            gap: 12px;
        }}

        .history-item-row {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 16px;
            background-color: var(--background);
            border: 1px solid #e2e8f0;
            border-radius: 12px;
            transition: all 0.2s;
        }}

        .history-item-row:hover {{
            border-color: var(--primary);
            box-shadow: 0 4px 12px rgba(0, 35, 111, 0.05);
        }}

        .history-item-meta {{
            display: flex;
            flex-direction: column;
            gap: 4px;
            max-width: 60%;
        }}

        .history-item-title {{
            font-size: 13px;
            font-weight: bold;
            color: var(--text-primary);
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }}

        .history-item-subtext {{
            font-size: 11px;
            color: var(--text-secondary);
        }}

        .history-item-score-badge {{
            background: var(--primary);
            color: #fff;
            padding: 6px 12px;
            border-radius: 8px;
            font-size: 14px;
            font-weight: 900;
        }}

        .history-btn-view {{
            background-color: #fff;
            border: 1px solid var(--primary);
            color: var(--primary);
            padding: 6px 12px;
            border-radius: 6px;
            font-size: 11px;
            font-weight: bold;
            cursor: pointer;
            transition: all 0.2s;
        }}

        .history-btn-view:hover {{
            background-color: var(--primary);
            color: #fff;
        }}

        /* ----------------------------------------------------- */
        /* TAB 3: Study Groups & Communities Styles */
        /* ----------------------------------------------------- */
        .groups-grid {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 20px;
            width: 100%;
            height: 100%;
            overflow-y: auto;
        }}

        .group-card {{
            background: #fff;
            border: 1px solid #cbd5e1;
            border-radius: 16px;
            padding: 24px;
            display: flex;
            flex-direction: column;
            gap: 12px;
            box-shadow: 0 4px 12px rgba(30, 58, 138, 0.02);
            position: relative;
        }}

        .group-status-badge {{
            position: absolute;
            top: 16px;
            right: 16px;
            background-color: #dcfce7;
            color: #15803d;
            font-size: 10px;
            font-weight: bold;
            padding: 4px 8px;
            border-radius: 999px;
        }}

        .group-header {{
            display: flex;
            align-items: center;
            gap: 12px;
        }}

        .group-icon-wrapper {{
            width: 48px;
            height: 48px;
            border-radius: 12px;
            background-color: var(--surface-container-high);
            display: flex;
            align-items: center;
            justify-content: center;
            color: var(--primary);
        }}

        .group-name {{
            font-size: 16px;
            font-weight: bold;
            color: var(--text-primary);
        }}

        .group-members {{
            font-size: 11px;
            color: var(--text-secondary);
        }}

        .group-desc {{
            font-size: 12px;
            color: var(--text-secondary);
            line-height: 1.6;
        }}

        .group-action-btn {{
            margin-top: auto;
            background-color: var(--primary);
            color: #fff;
            border: none;
            padding: 10px;
            border-radius: 8px;
            font-size: 12px;
            font-weight: bold;
            cursor: pointer;
            transition: opacity 0.2s;
        }}

        .group-action-btn:hover {{
            opacity: 0.9;
        }}

        /* ----------------------------------------------------- */
        /* TAB 4: Pro Benefits SaaS Tier */
        /* ----------------------------------------------------- */
        .pro-benefits-container {{
            width: 100%;
            height: 100%;
            display: flex;
            flex-direction: column;
            gap: 16px;
            overflow-y: auto;
        }}

        .pricing-grid {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 24px;
            max-width: 800px;
            margin: 0 auto;
        }}

        .tier-card {{
            background: #fff;
            border: 1px solid #cbd5e1;
            border-radius: 16px;
            padding: 32px;
            display: flex;
            flex-direction: column;
            gap: 16px;
            position: relative;
        }}

        .tier-card.featured {{
            border-color: var(--secondary);
            box-shadow: 0 10px 25px -5px rgba(0, 81, 213, 0.15);
        }}

        .featured-tag {{
            position: absolute;
            top: -12px;
            left: 50%;
            transform: translateX(-50%);
            background: linear-gradient(90deg, var(--primary) 0%, var(--secondary) 100%);
            color: #fff;
            font-size: 10px;
            font-weight: bold;
            padding: 4px 12px;
            border-radius: 999px;
            text-transform: uppercase;
        }}

        .tier-name {{
            font-size: 18px;
            font-weight: bold;
            color: var(--text-primary);
        }}

        .tier-price {{
            font-size: 32px;
            font-weight: 900;
            color: var(--primary);
        }}

        .tier-price-period {{
            font-size: 12px;
            font-weight: normal;
            color: var(--text-secondary);
        }}

        .features-list {{
            list-style: none;
            display: flex;
            flex-direction: column;
            gap: 12px;
            font-size: 13px;
            color: var(--text-secondary);
        }}

        .features-list li {{
            display: flex;
            align-items: center;
            gap: 8px;
        }}

        .features-list li .check-icon {{
            color: #166534;
            font-size: 16px;
        }}

        .tier-btn {{
            width: 100%;
            padding: 12px;
            border-radius: 8px;
            font-weight: bold;
            font-size: 13px;
            cursor: pointer;
            border: 1px solid var(--border-color);
            background: transparent;
            transition: all 0.2s;
        }}

        .tier-btn.active-btn {{
            background-color: var(--primary);
            color: #fff;
            border: none;
        }}

        .tier-btn.featured-btn {{
            background: linear-gradient(90deg, var(--primary) 0%, var(--secondary) 100%);
            color: #fff;
            border: none;
            box-shadow: 0 4px 10px rgba(0, 81, 213, 0.2);
        }}

        .tier-btn:hover {{
            transform: translateY(-1px);
        }}

        /* ----------------------------------------------------- */
        /* Interactive Modal System (弹窗样式) */
        /* ----------------------------------------------------- */
        .modal-overlay {{
            position: fixed;
            inset: 0;
            background: rgba(11, 28, 48, 0.4);
            backdrop-filter: blur(4px);
            z-index: 100;
            display: flex;
            align-items: center;
            justify-content: center;
            opacity: 0;
            pointer-events: none;
            transition: opacity 0.3s;
        }}

        .modal-overlay.active {{
            opacity: 1;
            pointer-events: auto;
        }}

        .modal-card {{
            background: #fff;
            border-radius: 16px;
            padding: 24px;
            width: 100%;
            max-width: 420px;
            box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
            transform: scale(0.9);
            transition: transform 0.3s;
            display: flex;
            flex-direction: column;
            gap: 16px;
            text-align: center;
        }}

        .modal-overlay.active .modal-card {{
            transform: scale(1);
        }}

        .modal-title {{
            font-size: 16px;
            font-weight: 800;
            color: var(--primary);
        }}

        .modal-body {{
            font-size: 12px;
            color: var(--text-secondary);
            line-height: 1.6;
        }}

        .modal-btn {{
            background-color: var(--primary);
            color: #fff;
            border: none;
            padding: 10px;
            border-radius: 8px;
            font-weight: bold;
            cursor: pointer;
        }}

        /* Animations */
        @keyframes spin {{
            0% {{ transform: rotate(0deg); }}
            100% {{ transform: rotate(360deg); }}
        }}

        /* Material Icons Standard Rendering Class */
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

    <!-- 1. Left Sidebar Navigation with switcher callbacks -->
    <aside>
        <div class="brand-section">
            <h1 class="brand-title">
                <span class="icon-symbol" style="font-size: 24px;">school</span>
                <span>雅思AI备考中心</span>
            </h1>
            <p class="brand-sub">Premium v2.5</p>
        </div>
        <nav>
            <a class="nav-link active" onclick="switchView('dash')" id="nav-dash">
                <span class="icon-symbol">dashboard</span>
                <span>Dashboard</span>
            </a>
            <a class="nav-link" onclick="switchView('history')" id="nav-history">
                <span class="icon-symbol">history</span>
                <span>Essay History</span>
            </a>
            <a class="nav-link" onclick="switchView('groups')" id="nav-groups">
                <span class="icon-symbol">group</span>
                <span>Study Groups</span>
            </a>
            <a class="nav-link" onclick="switchView('pro')" id="nav-pro">
                <span class="icon-symbol">workspace_premium</span>
                <span>Pro Benefits</span>
            </a>
        </nav>
        
        <div class="sidebar-footer">
            <div class="promo-card blue" onclick="openPromoModal('真题福利', '已经为您锁定 2026年最新雅思预测全套真题及官方范文包！请添加微信助理：<b>ielts_coach</b> 发送暗号“真题礼包”即可即刻获取下载通道。')">
                <div class="promo-header">
                    <span class="icon-symbol" style="font-variation-settings: 'FILL' 1">card_giftcard</span>
                    <span>🎁 独家备考福利</span>
                </div>
                <p class="promo-text">后台回复 “<b>雅思真题</b>” 即可免费领取 2026 最新预测及高分词汇表。</p>
            </div>
            
            <div class="promo-card indigo" onclick="openPromoModal('千人打卡群', '欢迎加入千人备考打卡群！群内每日进行写作互评与高分句型分享。请在添加微信 <b>ielts_coach</b> 后发送消息：“申请加入打卡群”，助教老师会在12小时内安排进群。')">
                <div class="promo-header">
                    <span class="icon-symbol" style="font-variation-settings: 'FILL' 1">groups</span>
                    <span>👥 互助打卡群</span>
                </div>
                <p class="promo-text">添加学长微信，备注 “<b>作文打卡</b>”，受邀加入千人雅思备考群。</p>
            </div>
            
            <div class="sidebar-bottom-row">
                <span>⚙️ DeepSeek-V3 Support</span>
                <span class="icon-symbol" onclick="openPromoModal('关于系统', '本系统深度适配最新版雅思官方写作四维标准，结合 DeepSeek-V3 高速推理算法，由雅思名校前教研组长联合深度研发调教，准确度高达 97% 以上。')" style="font-size:16px; cursor:pointer;">help_outline</span>
            </div>
        </div>
    </aside>

    <!-- 2. Top AppBar with triggerable modals -->
    <header>
        <div class="header-title-group">
            <span class="header-brand-name">IELTS AI Examiner Pro</span>
            <div class="header-tabs">
                <span class="header-tab-item active" onclick="highlightCriterion('TR')">TR</span>
                <span class="header-tab-item" onclick="highlightCriterion('CC')">CC</span>
                <span class="header-tab-item" onclick="highlightCriterion('LR')">LR</span>
                <span class="header-tab-item" onclick="highlightCriterion('GRA')">GRA</span>
            </div>
        </div>
        <div class="header-right">
            <button onclick="resetTest()" class="new-btn">
                <span class="icon-symbol" style="font-size:16px;">add</span>
                New Analysis
            </button>
            <button class="icon-btn" onclick="openNotificationModal()">
                <span class="icon-symbol">notifications</span>
            </button>
            <button class="icon-btn" onclick="openSettingsModal()">
                <span class="icon-symbol">settings</span>
            </button>
            
            <!-- Academic SVG High Fidelity Portrait Fallback -->
            <svg class="academic-avatar-svg" viewBox="0 0 100 100">
                <defs>
                    <clipPath id="circle-clip">
                        <circle cx="50" cy="50" r="45" />
                    </clipPath>
                </defs>
                <circle cx="50" cy="50" r="48" fill="#1e3a8a" />
                <g clip-path="url(#circle-clip)">
                    <circle cx="50" cy="38" r="18" fill="#dbeafe" />
                    <path d="M20,85 C20,62 30,55 50,55 C70,55 80,62 80,85" fill="#dbeafe" />
                    <rect x="42" y="58" width="16" height="10" fill="#1e3a8a" transform="rotate(45 50 60)"/>
                    <polygon points="50,45 42,55 58,55" fill="#00236f" />
                </g>
            </svg>
        </div>
    </header>

    <!-- 3. Main Body View Panel -->
    <main>
        
        <!-- ============================================================ -->
        <!-- VIEW 1: DASHBOARD主控制台 -->
        <!-- ============================================================ -->
        <div class="view-block active" id="view-dash">
            <!-- Left Panel: Form Submission -->
            <section class="left-panel">
                <div class="panel-header">
                    <h2 class="panel-title">
                        <span class="icon-symbol" style="color:var(--primary);">edit_note</span>
                        <span>📥 提交作文本系统</span>
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
                        <span>🚀 开始 AI 深度精批</span>
                    </button>
                </div>
            </section>

            <!-- Right Panel: Diagnostics Outputs -->
            <section class="right-panel">
                <div class="panel-header">
                    <h2 class="panel-title">
                        <span class="icon-symbol" style="color:var(--primary);">analytics</span>
                        <span>📊 AI 评估结果报告</span>
                    </h2>
                </div>
                
                <div class="right-viewport">
                    <!-- Default State (Empty Dashboard) -->
                    <div class="empty-state" id="emptyState">
                        <div class="empty-icon-circle">
                            <span class="icon-symbol" style="font-size:36px;">psychology</span>
                        </div>
                        <div>
                            <h3 class="empty-text-title">等待评估</h3>
                            <p class="empty-text-sub">💡 在左侧填写好题目和作文，点击“开始 AI 深度精批”，5秒内为您呈献满分改写与四维诊断报告。</p>
                        </div>
                    </div>

                    <!-- Loading Spinner Page -->
                    <div class="loading-overlay" id="loadingOverlay" style="display:none;">
                        <div class="spinner"></div>
                        <p class="loading-text">DeepSeek-V3 正在深度分析评测中...</p>
                        <p class="loading-sub">预计等待时间: 3秒</p>
                    </div>

                    <!-- Real Result Panel (Initially Hidden) -->
                    <div class="result-scroll-wrapper" id="analysisResult" style="display:none;">
                        <!-- Band Score Hero Header -->
                        <div class="score-hero-card">
                            <div>
                                <p class="score-label">Overall Band Score</p>
                                <h3 class="score-big-num" id="resOverall">7.5</h3>
                                <p class="score-level-desc" id="resLevel">Good User (C1 Advanced)</p>
                            </div>
                            <div class="sub-scores-grid">
                                <div class="sub-score-box" id="crit-TR">
                                    <p class="name">TR</p>
                                    <p class="val" id="resTR">7.0</p>
                                </div>
                                <div class="sub-score-box" id="crit-CC">
                                    <p class="name">CC</p>
                                    <p class="val" id="resCC">7.5</p>
                                </div>
                                <div class="sub-score-box" id="crit-LR">
                                    <p class="name">LR</p>
                                    <p class="val" id="resLR">8.0</p>
                                </div>
                                <div class="sub-score-box" id="crit-GRA">
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
        </div>

        <!-- ============================================================ -->
        <!-- VIEW 2: ESSAY HISTORY 历史档案 -->
        <!-- ============================================================ -->
        <div class="view-block" id="view-history">
            <div class="history-full-view">
                <div class="history-title-row">
                    <h2 class="panel-title" style="font-size: 18px;">
                        <span class="icon-symbol">history_edu</span>
                        <span>历史评估记录档案库</span>
                    </h2>
                    <span class="panel-badge" id="history-count">共 1 条记录</span>
                </div>
                <div class="history-scroll-container" id="historyListContainer">
                    <!-- Rendered dynamically by Javascript -->
                </div>
            </div>
        </div>

        <!-- ============================================================ -->
        <!-- VIEW 3: STUDY GROUPS 互助打卡群 -->
        <!-- ============================================================ -->
        <div class="view-block" id="view-groups">
            <div class="groups-grid">
                <div class="group-card">
                    <span class="group-status-badge">推荐加入</span>
                    <div class="group-header">
                        <div class="group-icon-wrapper">
                            <span class="icon-symbol" style="font-size: 24px; font-variation-settings: 'FILL' 1;">forum</span>
                        </div>
                        <div>
                            <h3 class="group-name">雅思写作7.5分突击打卡群</h3>
                            <p class="group-members">2,481 名成员正在打卡</p>
                        </div>
                    </div>
                    <p class="group-desc">
                        主要讨论学术写作的高分核心句式转换、高级同义替换和考官审题思路避坑。每天提供雅思大作文题目实操。
                    </p>
                    <button class="group-action-btn" onclick="openPromoModal('写作高分打卡群', '已为你生成专场入群邀请：\\n请直接添加助教微信 <b>ielts_coach</b>，发送入群申请“<b>作文打卡群</b>”。我们会在极短时间内拉你入群，并同步发放第一份群福利！')">一键申请入群</button>
                </div>

                <div class="group-card">
                    <span class="group-status-badge" style="background-color:#eff6ff; color:#1e40af;">机经独享</span>
                    <div class="group-header">
                        <div class="group-icon-wrapper" style="color:var(--secondary);">
                            <span class="icon-symbol" style="font-size: 24px; font-variation-settings: 'FILL' 1;">campaign</span>
                        </div>
                        <div>
                            <h3 class="group-name">2026口语官方考官一对一模拟营</h3>
                            <p class="group-members">1,219 名成员正在参加</p>
                        </div>
                    </div>
                    <p class="group-desc">
                        前雅思考官主持，定期在群内进行模拟考官问答，现场连线打分。提供第一手核心机经和最地道的表达纠错。
                    </p>
                    <button class="group-action-btn" style="background-color:var(--secondary);" onclick="openPromoModal('考官口语群', '恭喜！2026年口语一对一模拟群当前还有空余名额：\\n请添加教研助理微信 <b>ielts_coach</b> 发送消息：“<b>口语一对一模拟</b>”，我们将发送给你群入口和下一场连线时间表！')">加入考官模拟营</button>
                </div>
            </div>
        </div>

        <!-- ============================================================ -->
        <!-- VIEW 4: PRO BENEFITS 会员尊享权益 -->
        <!-- ============================================================ -->
        <div class="view-block" id="view-pro">
            <div class="pro-benefits-container">
                <div class="history-title-row" style="max-width: 800px; margin: 0 auto; width: 100%;">
                    <h2 class="panel-title" style="font-size: 18px;">
                        <span class="icon-symbol" style="color:var(--secondary);">workspace_premium</span>
                        <span>升级会员解锁考官极速精批</span>
                    </h2>
                </div>
                <div class="pricing-grid">
                    <!-- Standard Tier Card -->
                    <div class="tier-card">
                        <h3 class="tier-name">普通备考员 (Free)</h3>
                        <p class="tier-price">¥0 <span class="tier-price-period">/ 永不收费</span></p>
                        <ul class="features-list">
                            <li><span class="icon-symbol check-icon">check_circle</span> 每日免费评测限额 3 次</li>
                            <li><span class="icon-symbol check-icon">check_circle</span> 标准四维评测拆解建议</li>
                            <li><span class="icon-symbol check-icon">check_circle</span> DeepSeek-V3 标准通道</li>
                        </ul>
                        <button class="tier-btn active-btn" disabled>当前正在享用</button>
                    </div>

                    <!-- Featured Pro Tier Card -->
                    <div class="tier-card featured">
                        <div class="featured-tag">最受欢迎</div>
                        <h3 class="tier-name">考官级特权会员 (Pro Premium)</h3>
                        <p class="tier-price" style="color:var(--secondary);">¥29 <span class="tier-price-period">/ 按月度计费</span></p>
                        <ul class="features-list">
                            <li><span class="icon-symbol check-icon" style="color:var(--secondary);">check_circle</span> 无限次作文打分、批改</li>
                            <li><span class="icon-symbol check-icon" style="color:var(--secondary);">check_circle</span> 满分改写范文导出 PDF 电子档</li>
                            <li><span class="icon-symbol check-icon" style="color:var(--secondary);">check_circle</span> 优先享有高速专属接口（秒级响应）</li>
                            <li><span class="icon-symbol check-icon" style="color:var(--secondary);">check_circle</span> 每周考官级作文解题思路推导推送</li>
                        </ul>
                        <button class="tier-btn featured-btn" onclick="openPaymentModal()">一键升级解锁无限额度</button>
                    </div>
                </div>
            </div>
        </div>
    </main>

    <!-- Interactive Modular Overlay Modals -->
    <div class="modal-overlay" id="commonModalOverlay" onclick="closeCommonModal()">
        <div class="modal-card" onclick="event.stopPropagation()">
            <h3 class="modal-title" id="commonModalTitle">温馨福利提示</h3>
            <div class="modal-body" id="commonModalBody">
                内容加载中...
            </div>
            <button class="modal-btn" onclick="closeCommonModal()">确认并关闭</button>
        </div>
    </div>

    <script>
        const aiOutput = {js_ai_output};
        const lastEssay = {js_last_essay};
        const lastPrompt = {js_last_prompt};
        const lastTask = {js_last_task};
        const essayHistory = {js_essay_history};
        const stLoading = {js_loading_status};
        const apiConfigured = {js_api_configured};

        // Window Initializer & Data Loaders
        window.onload = function() {{
            // 恢复上一次作文题目与具体内容
            if (lastEssay) document.getElementById('essayInput').value = lastEssay;
            if (lastPrompt) document.getElementById('promptInput').value = lastPrompt;
            if (lastTask) document.getElementById('taskSelect').value = lastTask;
            updateWordCount();

            // 渲染历史档案列表
            renderHistoryList();

            // 视窗控制初始化
            if (stLoading) {{
                switchView('dash');
                document.getElementById('loadingOverlay').style.display = 'flex';
                document.getElementById('emptyState').style.display = 'none';
                document.getElementById('analysisResult').style.display = 'none';
            }} else if (aiOutput) {{
                switchView('dash');
                document.getElementById('loadingOverlay').style.display = 'none';
                document.getElementById('emptyState').style.display = 'none';
                
                if (aiOutput.error) {{
                    alert("考官接口请求发生错误: " + aiOutput.error);
                    document.getElementById('emptyState').style.display = 'flex';
                }} else {{
                    // 装填并点亮全新高定学术看板
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

        // Tab switcher to switch views (Dash, History, Groups, Pro)
        function switchView(viewId) {{
            // 样式更新：移除所有菜单的激活激活态
            document.querySelectorAll('nav .nav-link').forEach(link => link.classList.remove('active'));
            const targetLink = document.getElementById('nav-' + viewId);
            if (targetLink) targetLink.classList.add('active');

            // 视图切换
            document.querySelectorAll('.view-block').forEach(block => block.classList.remove('active'));
            const targetBlock = document.getElementById('view-' + viewId);
            if (targetBlock) targetBlock.classList.add('active');
        }}

        // Highlights specific evaluation criterion inside the radar dashboard
        function highlightCriterion(criterion) {{
            // 移除其它高亮
            document.querySelectorAll('.sub-score-box').forEach(box => {{
                box.style.borderColor = "#cbd5e1";
                box.style.backgroundColor = "var(--background)";
            }});
            
            // 为选中目标添加高亮外框
            const targetBox = document.getElementById('crit-' + criterion);
            if (targetBox) {{
                targetBox.style.borderColor = "var(--primary)";
                targetBox.style.backgroundColor = "var(--surface-container-high)";
            }}
        }}

        // Render evaluation history dynamically inside History Tab
        function renderHistoryList() {{
            const container = document.getElementById('historyListContainer');
            document.getElementById('history-count').innerText = `共 ${{essayHistory.length}} 条评估记录`;
            container.innerHTML = "";

            if (essayHistory.length === 0) {{
                container.innerHTML = `
                    <div style="text-align:center; padding: 48px; color:var(--text-secondary);">
                        <span class="icon-symbol" style="font-size:48px; margin-bottom:12px;">history_edu</span>
                        <p>暂无任何历史评估。快在 Dashboard 批改你的第一篇大作吧！</p>
                    </div>
                `;
                return;
            }}

            essayHistory.forEach(record => {{
                const row = document.createElement('div');
                row.className = "history-item-row";
                row.innerHTML = `
                    <div class="history-item-meta">
                        <p class="history-item-title">${{record.prompt}}</p>
                        <p class="history-item-subtext">📅 测评时间: ${{record.date}} | 📝 类型: ${{record.task}}</p>
                    </div>
                    <div style="display:flex; align-items:center; gap: 16px;">
                        <span class="history-item-score-badge">${{record.overall}}分</span>
                        <button onclick="loadHistoryItem('${{record.id}}')" class="history-btn-view">查看解析看版</button>
                    </div>
                `;
                container.appendChild(row);
            }});
        }}

        // Triggers loading historical item details back into Dashboard
        function loadHistoryItem(id) {{
            const targetUrl = window.parent.location.origin + window.parent.location.pathname + "?load_history_id=" + id;
            window.parent.location.href = targetUrl;
        }}

        // Trigger analysis
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

            // 通过 URL 回传向 Streamlit 触发 Rerun 任务
            const targetUrl = window.parent.location.origin + window.parent.location.pathname + 
                "?task=" + encodeURIComponent(task) + 
                "&prompt=" + encodeURIComponent(prompt) + 
                "&essay=" + encodeURIComponent(essay);
            
            window.parent.location.href = targetUrl;
        }}

        // Reset inputs and page parameters
        function resetTest() {{
            document.getElementById('essayInput').value = "";
            document.getElementById('promptInput').value = "";
            updateWordCount();
            window.parent.location.href = window.parent.location.origin + window.parent.location.pathname;
        }}

        // Word Counter
        function updateWordCount() {{
            const text = document.getElementById('essayInput').value.trim();
            const count = text ? text.split(/\\s+/).length : 0;
            document.getElementById('wordCount').innerText = `Word Count: ${{count}} words`;
        }}

        // Copy essay text to clipboard
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

        // Modal Helpers
        function openPromoModal(title, body) {{
            document.getElementById('commonModalTitle').innerText = title;
            document.getElementById('commonModalBody').innerHTML = body.replace(/\\n/g, '<br>');
            document.getElementById('commonModalOverlay').classList.add('active');
        }}

        function closeCommonModal() {{
            document.getElementById('commonModalOverlay').classList.remove('active');
        }}

        // SaaS Payment Integration simulator
        function openPaymentModal() {{
            openPromoModal('🔐 开启升级会员特权', `
                <div style="display:flex; flex-direction:column; align-items:center; gap:12px;">
                    <p>正在生成微信/支付宝定制安全升级支付通道...</p>
                    <div style="background-color:#eff4ff; border:2px dashed var(--primary); padding:16px; border-radius:12px; font-weight:bold; color:var(--primary); font-size:14px; width:100%;">
                        🔍 模拟支付中 (¥29/月)<br>
                        <span style="font-size:11px; color:var(--text-secondary); font-weight:normal;">正式商用版本可直接绑定微信/支付宝商户收款二维码及自动回调解锁接口。</span>
                    </div>
                </div>
            `);
        }}

        // Header Notification center simulator
        function openNotificationModal() {{
            openPromoModal('🔔 雅思AI测评中心通知', `
                <div style="text-align:left; display:flex; flex-direction:column; gap:8px;">
                    <p style="border-bottom:1px solid #e2e8f0; padding-bottom:6px;"><b>🆕 系统更新 (2026年5月30日):</b><br>DeepSeek-V3 推理加速通道深度优化完毕，单次测评速度已缩短至 3-5 秒左右。</p>
                    <p><b>📅 考情公告:</b><br>2026年6月雅思大作文官方机经预测与口语高频新题题库已更新至群文件中，点击左下角福利群加入获取。</p>
                </div>
            `);
        }}

        // Settings modal simulator
        function openSettingsModal() {{
            openPromoModal('⚙️ 系统偏好配置 (Settings)', `
                <div style="text-align:left; display:flex; flex-direction:column; gap:12px;">
                    <div>
                        <label style="font-weight:bold; font-size:11px;">🚀 评测大模型引擎：</label>
                        <select style="padding:6px; margin-top:4px;"><option>DeepSeek-V3 (极速高智商)</option><option>DeepSeek-R1 (深度长思考)</option></select>
                    </div>
                    <div>
                        <label style="font-weight:bold; font-size:11px;">🎯 目标冲刺分数：</label>
                        <select style="padding:6px; margin-top:4px;"><option>7.0 分冲刺营</option><option>7.5 分学霸营</option><option>8.0 分极客营</option></select>
                    </div>
                    <p style="font-size:10px; color:var(--text-secondary);">配置更改后将自动保存在您的专属浏览器本地缓存中。</p>
                </div>
            `);
        }}
    </script>
</body>
</html>
"""

# 8. 全屏一键无缝注入
st.components.v1.html(HTML_TEMPLATE, height=720, scrolling=False)
