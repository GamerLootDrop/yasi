import streamlit as st
import json
from openai import OpenAI

# 1. 强制覆盖并接管 Streamlit 的原生样式，使其达到 100% 全屏无边界 HTML 体验
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

# 7. 完整还原、融汇、进化的前端高定页面模板
HTML_TEMPLATE = f"""
<!DOCTYPE html>
<html class="light" lang="en">
<head>
    <meta charset="utf-8"/>
    <meta content="width=device-width, initial-scale=1.0" name="viewport"/>
    <title>IELTS AI Examiner Pro - Dashboard</title>
    <script src="[https://cdn.tailwindcss.com?plugins=forms,container-queries](https://cdn.tailwindcss.com?plugins=forms,container-queries)"></script>
    <link href="[https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap](https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap)" rel="stylesheet"/>
    <link href="[https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap](https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap)" rel="stylesheet"/>
    <script id="tailwind-config">
        tailwind.config = {{
            darkMode: "class",
            theme: {{
                extend: {{
                    "colors": {{
                        "on-error-container": "#93000a",
                        "surface-container-high": "#dce9ff",
                        "on-tertiary-container": "#f39461",
                        "primary-fixed": "#dce1ff",
                        "on-surface-variant": "#444651",
                        "on-secondary": "#ffffff",
                        "tertiary-fixed": "#ffdbcb",
                        "secondary-fixed-dim": "#b4c5ff",
                        "primary": "#00236f",
                        "surface": "#f8f9ff",
                        "error-container": "#ffdad6",
                        "background": "#f8f9ff",
                        "on-secondary-fixed": "#00174b",
                        "on-primary-fixed-variant": "#264191",
                        "secondary-fixed": "#dbe1ff",
                        "surface-container-low": "#eff4ff",
                        "surface-container-highest": "#d3e4fe",
                        "surface-bright": "#f8f9ff",
                        "on-secondary-container": "#fefcff",
                        "inverse-primary": "#b6c4ff",
                        "on-tertiary": "#ffffff",
                        "on-surface": "#0b1c30",
                        "inverse-on-surface": "#eaf1ff",
                        "outline-variant": "#c5c5d3",
                        "on-primary-container": "#90a8ff",
                        "primary-fixed-dim": "#b6c4ff",
                        "secondary": "#0051d5",
                        "on-primary": "#ffffff",
                        "on-background": "#0b1c30",
                        "surface-variant": "#d3e4fe",
                        "on-tertiary-fixed": "#341100",
                        "inverse-surface": "#213145",
                        "on-error": "#ffffff",
                        "on-secondary-fixed-variant": "#003ea8",
                        "on-primary-fixed": "#00164e",
                        "surface-container": "#e5eeff",
                        "surface-tint": "#4059aa",
                        "error": "#ba1a1a",
                        "on-tertiary-fixed-variant": "#773205",
                        "surface-container-lowest": "#ffffff",
                        "tertiary-container": "#6e2c00",
                        "surface-dim": "#cbdbf5",
                        "primary-container": "#1e3a8a",
                        "outline": "#757682",
                        "tertiary": "#4b1c00",
                        "tertiary-fixed-dim": "#ffb691",
                        "secondary-container": "#316bf3"
                    }}
                }}
            }}
        }}
    </script>
    <style>
        body {{ font-family: 'Inter', sans-serif; }}
        .material-symbols-outlined {{
            font-variation-settings: 'FILL' 0, 'wght' 400, 'GRAD' 0, 'opsz' 24;
        }}
        .academic-shadow {{
            box-shadow: 0 4px 6px -1px rgba(30, 58, 138, 0.05), 0 2px 4px -1px rgba(30, 58, 138, 0.03);
        }}
        .writing-pane {{
            scrollbar-width: thin;
            scrollbar-color: #cbd5e1 #f8f9ff;
        }}
    </style>
</head>
<body class="bg-background text-on-background overflow-hidden">

    <!-- 1. Left Sidebar Navigation Shell -->
    <aside class="fixed left-0 top-0 h-full w-[280px] bg-surface-container-low shadow-sm flex flex-col p-6 z-50 border-r border-slate-100">
        <div class="mb-8">
            <h1 class="text-xl font-black text-primary mb-1 flex items-center gap-1">🎓 雅思AI备考中心</h1>
            <p class="text-on-surface-variant text-[11px] font-bold opacity-70 uppercase tracking-widest">Premium v2.5</p>
        </div>
        <nav class="flex-1 space-y-2">
            <a id="nav-dash" class="flex items-center gap-3 px-4 py-3 rounded-lg text-primary font-bold border-r-4 border-primary bg-surface-container-high transition-colors" href="#">
                <span class="material-symbols-outlined">dashboard</span>
                <span>Dashboard</span>
            </a>
            <a id="nav-history" class="flex items-center gap-3 px-4 py-3 rounded-lg text-on-surface-variant hover:bg-surface-container transition-colors" href="#">
                <span class="material-symbols-outlined">history</span>
                <span>Essay History</span>
            </a>
            <a id="nav-groups" class="flex items-center gap-3 px-4 py-3 rounded-lg text-on-surface-variant hover:bg-surface-container transition-colors" href="#">
                <span class="material-symbols-outlined">group</span>
                <span>Study Groups</span>
            </a>
            <a id="nav-pro" class="flex items-center gap-3 px-4 py-3 rounded-lg text-on-surface-variant hover:bg-surface-container transition-colors" href="#">
                <span class="material-symbols-outlined">workspace_premium</span>
                <span>Pro Benefits</span>
            </a>
        </nav>
        <div class="mt-auto space-y-4">
            <!-- Benefit Card 1 (Blue) -->
            <div class="bg-primary-container text-on-primary-fixed p-4 rounded-xl academic-shadow border border-blue-100/50">
                <div class="flex items-center gap-2 mb-2">
                    <span class="material-symbols-outlined text-primary" style="font-variation-settings: 'FILL' 1">card_giftcard</span>
                    <span class="text-xs font-bold text-primary">🎁 独家备考福利</span>
                </div>
                <p class="text-[11px] leading-relaxed text-slate-600">后台回复 “<b>雅思真题</b>” 即可免费领取 2026 最新雅思考试机经预测及高分词汇表。</p>
            </div>
            <!-- Benefit Card 2 (Green/Purple) -->
            <div class="bg-indigo-50 text-indigo-950 p-4 rounded-xl academic-shadow border border-indigo-100">
                <div class="flex items-center gap-2 mb-2">
                    <span class="material-symbols-outlined text-indigo-700" style="font-variation-settings: 'FILL' 1">groups</span>
                    <span class="text-xs font-bold text-indigo-800">👥 互助打卡群</span>
                </div>
                <p class="text-[11px] leading-relaxed opacity-90">添加学长微信，备注 “<b>作文打卡</b>”，受邀加入千人雅思备考群。</p>
            </div>
            <div class="pt-4 border-t border-outline-variant flex items-center justify-between">
                <span class="text-[10px] font-bold text-on-surface-variant">⚙️ DeepSeek-V3 Support</span>
                <span class="material-symbols-outlined text-outline cursor-pointer hover:text-primary">help_outline</span>
            </div>
        </div>
    </aside>

    <!-- 2. Top AppBar Shell -->
    <header class="fixed top-0 left-[280px] right-0 h-16 bg-surface border-b border-outline-variant flex items-center justify-between px-8 z-40">
        <div class="flex items-center gap-8">
            <span class="text-md font-black text-primary tracking-tight">IELTS AI Examiner Pro</span>
            <div class="flex gap-4">
                <span class="text-primary border-b-2 border-primary pb-1 font-bold text-xs cursor-pointer">TR</span>
                <span class="text-on-surface-variant hover:text-primary transition-all font-semibold text-xs cursor-pointer">CC</span>
                <span class="text-on-surface-variant hover:text-primary transition-all font-semibold text-xs cursor-pointer">LR</span>
                <span class="text-on-surface-variant hover:text-primary transition-all font-semibold text-xs cursor-pointer">GRA</span>
            </div>
        </div>
        <div class="flex items-center gap-4">
            <button onclick="resetTest()" class="bg-primary text-on-primary px-4 py-2 rounded-lg text-xs font-bold hover:opacity-90 active:scale-95 duration-200 transition-all flex items-center gap-1.5">
                <span class="material-symbols-outlined text-[16px]">add</span>
                New Analysis
            </button>
            <span class="material-symbols-outlined text-outline cursor-pointer hover:text-primary">notifications</span>
            <span class="material-symbols-outlined text-outline cursor-pointer hover:text-primary">settings</span>
            <div class="w-8 h-8 rounded-full bg-surface-container-highest overflow-hidden border border-outline-variant">
                <img alt="User Avatar" class="w-full h-full object-cover" src="[https://lh3.googleusercontent.com/aida-public/AB6AXuA6OsXNWZ68DPQHc81CV6O6_nnxwGSPx2rK82Km0XDB5dMrJIdt6eewicggxVE44SPbbqDv-QJnxSB8yYSfOXC0-DcoETi4yO9e2S_wGGwqVaMlQJd8TkRncoVcFw3Fi9JzmWlNujI6mHKhmOx4MoDrLLAngvmaW-5dZD1lZTxYLsXeu_IK6Lq-0gd4YmvT2YxSTk35vkiqcyZLXI8CI9WmkaysWRl_uFesTx6vL9RSwEteK5Esa63RaMTi884rqIlfnbzFn216jg](https://lh3.googleusercontent.com/aida-public/AB6AXuA6OsXNWZ68DPQHc81CV6O6_nnxwGSPx2rK82Km0XDB5dMrJIdt6eewicggxVE44SPbbqDv-QJnxSB8yYSfOXC0-DcoETi4yO9e2S_wGGwqVaMlQJd8TkRncoVcFw3Fi9JzmWlNujI6mHKhmOx4MoDrLLAngvmaW-5dZD1lZTxYLsXeu_IK6Lq-0gd4YmvT2YxSTk35vkiqcyZLXI8CI9WmkaysWRl_uFesTx6vL9RSwEteK5Esa63RaMTi884rqIlfnbzFn216jg)"/>
            </div>
        </div>
    </header>

    <!-- 3. Main Content Canvas -->
    <main class="ml-[280px] mt-16 p-6 h-[calc(100vh-64px)] flex gap-6 overflow-hidden">
        
        <!-- Left Column: Submission Panel -->
        <section class="w-[45%] flex flex-col gap-4">
            <div class="flex items-center justify-between">
                <h2 class="text-md font-extrabold text-primary flex items-center gap-1.5">
                    <span class="material-symbols-outlined text-primary">edit_note</span>
                    📥 提交作文本系统
                </h2>
                <span class="text-[10px] bg-surface-container-high px-2 py-1 rounded text-primary font-bold">Academic Mode</span>
            </div>
            
            <div class="bg-surface-container-lowest border border-outline-variant rounded-xl academic-shadow p-6 flex-1 flex flex-col gap-4">
                <!-- Task Type -->
                <div class="space-y-1">
                    <label class="text-xs font-bold text-on-surface-variant block">📝 选择你的作文类型 (Task Type)</label>
                    <select id="taskSelect" class="w-full rounded-lg border-outline-variant focus:ring-primary focus:border-primary text-sm">
                        <option value="IELTS Academic Task 2 (Essay)">IELTS Academic Task 2 (Essay)</option>
                        <option value="IELTS Academic Task 1 (Report/Data)">IELTS Academic Task 1 (Report/Data)</option>
                        <option value="IELTS General Training Task 1 (Letter)">IELTS General Training Task 1 (Letter)</option>
                    </select>
                </div>
                <!-- Prompt -->
                <div class="space-y-1">
                    <label class="text-xs font-bold text-on-surface-variant block">📌 输入作文题目 (Prompt/Question)</label>
                    <textarea id="promptInput" class="w-full rounded-lg border-outline-variant focus:ring-primary focus:border-primary text-sm resize-none" placeholder="Type or paste the exam question here..." rows="3"></textarea>
                </div>
                <!-- Essay Area -->
                <div class="space-y-1 flex-1 flex flex-col">
                    <label class="text-xs font-bold text-on-surface-variant block">✍️ 粘贴你的文章 (Your Essay)</label>
                    <textarea id="essayInput" oninput="updateWordCount()" class="flex-1 w-full rounded-lg border-outline-variant focus:ring-primary focus:border-primary text-sm writing-pane p-4" placeholder="Start writing or paste your essay content here. Minimum 250 words recommended for Task 2..."></textarea>
                    <div class="flex justify-end pt-1">
                        <span id="wordCount" class="text-[11px] font-semibold text-outline">Word Count: 0 words</span>
                    </div>
                </div>
                <!-- CTA Button -->
                <button onclick="startAnalysis()" class="w-full py-3 rounded-xl bg-gradient-to-r from-primary to-secondary text-on-primary font-bold hover:scale-[1.01] active:scale-[0.98] transition-all flex items-center justify-center gap-2" id="startAnalysisBtn">
                    <span class="material-symbols-outlined">rocket_launch</span>
                    🚀 开始 AI 深度精批
                </button>
            </div>
        </section>

        <!-- Right Column: Analysis Output -->
        <section class="flex-1 flex flex-col gap-4">
            <h2 class="text-md font-extrabold text-primary flex items-center gap-1.5">
                <span class="material-symbols-outlined text-primary">analytics</span>
                📊 AI 评估结果报告
            </h2>
            <div class="flex-1 relative overflow-hidden" id="resultsContainer">
                
                <!-- Default State (Empty Card) -->
                <div class="absolute inset-0 bg-surface-container-low border-2 border-dashed border-outline-variant rounded-xl flex flex-col items-center justify-center p-8 text-center space-y-4" id="emptyState">
                    <div class="w-16 h-16 rounded-full bg-surface-container-high flex items-center justify-center text-primary-container">
                        <span class="material-symbols-outlined text-[36px]" style="font-variation-settings: 'opsz' 36">psychology</span>
                    </div>
                    <div class="max-w-sm space-y-1.5">
                        <h3 class="text-sm font-extrabold text-on-surface">等待评估</h3>
                        <p class="text-xs text-on-surface-variant leading-relaxed">💡 在左侧填写好题目和作文，点击“开始 AI 深度精批”，5秒内为您呈献满分改写与四维诊断报告。</p>
                    </div>
                </div>

                <!-- Analysis Results (Hidden by default, shown dynamically via JS) -->
                <div class="hidden absolute inset-0 overflow-y-auto writing-pane pr-2 space-y-4" id="analysisResult">
                    
                    <!-- Band Score Hero Card -->
                    <div class="bg-white border border-outline-variant rounded-xl academic-shadow p-6 flex items-center justify-between">
                        <div>
                            <p class="text-[10px] text-slate-400 font-black uppercase tracking-wider">Overall Band Score</p>
                            <h3 id="resOverall" class="text-5xl font-black text-primary">7.5</h3>
                            <p id="resLevel" class="text-xs text-secondary font-bold mt-1">Good User (C1 Advanced)</p>
                        </div>
                        <div class="grid grid-cols-2 gap-2">
                            <div class="bg-slate-50 px-3 py-1.5 rounded-lg text-center border border-slate-100 min-w-[55px]">
                                <p class="text-[9px] text-slate-400 font-black">TR</p>
                                <p id="resTR" class="text-md font-bold text-primary">7.0</p>
                            </div>
                            <div class="bg-slate-50 px-3 py-1.5 rounded-lg text-center border border-slate-100 min-w-[55px]">
                                <p class="text-[9px] text-slate-400 font-black">CC</p>
                                <p id="resCC" class="text-md font-bold text-primary">7.5</p>
                            </div>
                            <div class="bg-slate-50 px-3 py-1.5 rounded-lg text-center border border-slate-100 min-w-[55px]">
                                <p class="text-[9px] text-slate-400 font-black">LR</p>
                                <p id="resLR" class="text-md font-bold text-primary">8.0</p>
                            </div>
                            <div class="bg-slate-50 px-3 py-1.5 rounded-lg text-center border border-slate-100 min-w-[55px]">
                                <p class="text-[9px] text-slate-400 font-black">GRA</p>
                                <p id="resGRA" class="text-md font-bold text-primary">7.0</p>
                            </div>
                        </div>
                    </div>

                    <!-- Bento Box Feedback Card -->
                    <div class="grid grid-cols-2 gap-4">
                        <!-- Strengths -->
                        <div class="bg-white border-l-4 border-l-secondary rounded-xl academic-shadow p-4 border border-outline-variant">
                            <div class="flex items-center gap-2 mb-2">
                                <span class="material-symbols-outlined text-secondary font-black" style="font-variation-settings: 'FILL' 1">verified</span>
                                <span class="text-xs font-bold text-secondary">优势亮点 (Strengths)</span>
                            </div>
                            <ul class="space-y-1.5 text-xs text-slate-600 leading-relaxed">
                                <li id="resS1">• [亮点1]</li>
                                <li id="resS2">• [亮点2]</li>
                            </ul>
                        </div>
                        <!-- Improvements -->
                        <div class="bg-white border-l-4 border-l-error rounded-xl academic-shadow p-4 border border-outline-variant">
                            <div class="flex items-center gap-2 mb-2">
                                <span class="material-symbols-outlined text-error font-black" style="font-variation-settings: 'FILL' 1">report</span>
                                <span class="text-xs font-bold text-error">改进建议 (Areas for Improvement)</span>
                            </div>
                            <ul class="space-y-1.5 text-xs text-slate-600 leading-relaxed">
                                <li id="resI1" class="flex gap-1"><span class="text-error font-bold">•</span><span>[建议1]</span></li>
                                <li id="resI2" class="flex gap-1"><span class="text-error font-bold">•</span><span>[建议2]</span></li>
                            </ul>
                        </div>
                    </div>

                    <!-- AI Rewriting Showcase Card -->
                    <div class="bg-white border border-outline-variant rounded-xl academic-shadow p-5">
                        <div class="flex items-center justify-between mb-2">
                            <h4 class="text-xs font-extrabold text-[#00236f]">✨ AI 满分改写建议 (Refinement)</h4>
                            <button onclick="copyModelEssay()" class="text-primary text-[11px] font-bold flex items-center gap-1 hover:underline">
                                <span class="material-symbols-outlined text-[14px]">content_copy</span> Copy Essay
                            </button>
                        </div>
                        <div id="resRefinement" class="p-4 bg-slate-50 rounded-lg text-xs italic text-slate-600 border border-slate-100 leading-relaxed whitespace-pre-wrap">
                            "Model essay placeholder..."
                        </div>
                        <div class="mt-4 grid grid-cols-2 gap-4">
                            <div class="p-3 bg-slate-50 rounded border border-slate-100">
                                <p class="text-[9px] text-slate-400 font-bold uppercase">Vocabulary Boost</p>
                                <p id="resVocab" class="text-xs mt-1">Instead of "bad effect", use <span class="text-secondary font-bold">"detrimental impact"</span></p>
                            </div>
                            <div class="p-3 bg-slate-50 rounded border border-slate-100">
                                <p class="text-[9px] text-slate-400 font-bold uppercase">Grammar Fix</p>
                                <p id="resGrammar" class="text-xs mt-1">Correction: <span class="text-red-500 line-through">"The research show"</span> → <span class="text-secondary font-bold">"shows"</span></p>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Loading State Overlay -->
                <div class="hidden absolute inset-0 bg-white/85 backdrop-blur-xs z-10 flex flex-col items-center justify-center space-y-3" id="loadingOverlay">
                    <div class="w-10 h-10 border-4 border-primary/20 border-t-primary rounded-full animate-spin"></div>
                    <p class="text-primary font-bold text-sm">DeepSeek-V3 正在深度分析评测中...</p>
                    <p class="text-on-surface-variant text-[10px] font-semibold opacity-80">预计等待时间: 3秒</p>
                </div>
            </div>
        </section>
    </main>

    <!-- Global Watermark Decoration -->
    <div class="fixed bottom-4 right-4 pointer-events-none opacity-40">
        <img alt="British Council Branding" class="w-12 h-12 object-contain" src="[https://lh3.googleusercontent.com/aida-public/AB6AXuCq8sxODXxAXBxSUcisb44SNIFUxvaWJm6xgfNYJz5w6I0XGSgDdDF4sbHCo_HlVkGZfTFYaHzXLxVMLBXAUWObMerq-O2jZ-GuWQ-LQvXq-Ecy8KZl4FQRVkhlBp8hGUtBR_aIK7Uhn49GgSfGa_CnKLoqv45YLsqIsjbUiImF2w0pFYYCNsimc5d0IJrksk6s1BIcYMUgfXb_NinfTuVtf5Gl07AJ8pA3F-ehOnHE9bOeX2U8EaAhRWFBHJ1WUe4EukL0MBB63Q](https://lh3.googleusercontent.com/aida-public/AB6AXuCq8sxODXxAXBxSUcisb44SNIFUxvaWJm6xgfNYJz5w6I0XGSgDdDF4sbHCo_HlVkGZfTFYaHzXLxVMLBXAUWObMerq-O2jZ-GuWQ-LQvXq-Ecy8KZl4FQRVkhlBp8hGUtBR_aIK7Uhn49GgSfGa_CnKLoqv45YLsqIsjbUiImF2w0pFYYCNsimc5d0IJrksk6s1BIcYMUgfXb_NinfTuVtf5Gl07AJ8pA3F-ehOnHE9bOeX2U8EaAhRWFBHJ1WUe4EukL0MBB63Q)"/>
    </div>

    <!-- 4. Pure Frontend JavaScript Bridge Controller -->
    <script>
        const aiOutput = {js_ai_output};
        const lastEssay = {js_last_essay};
        const lastPrompt = {js_last_prompt};
        const lastTask = {js_last_task};
        const stLoading = {js_loading_status};
        const apiConfigured = {js_api_configured};

        // 页面初始化加载数据回显与视图控制
        window.onload = function() {{
            // 恢复上一次的输入
            if (lastEssay) document.getElementById('essayInput').value = lastEssay;
            if (lastPrompt) document.getElementById('promptInput').value = lastPrompt;
            if (lastTask) document.getElementById('taskSelect').value = lastTask;
            updateWordCount();

            // 如果后端正在拼装加载
            if (stLoading) {{
                document.getElementById('loadingOverlay').classList.remove('hidden');
                document.getElementById('emptyState').classList.add('hidden');
                document.getElementById('analysisResult').classList.add('hidden');
            }} else if (aiOutput) {{
                document.getElementById('loadingOverlay').classList.add('hidden');
                document.getElementById('emptyState').classList.add('hidden');
                
                if (aiOutput.error) {{
                    alert("错误：\\n" + aiOutput.error);
                    document.getElementById('emptyState').classList.remove('hidden');
                }} else {{
                    // 开始往高定 Tailwind UI 模板中实时渲染真实 API 数据
                    document.getElementById('resOverall').innerText = aiOutput.overall || "5.5";
                    document.getElementById('resLevel').innerText = aiOutput.level || "Band Score";
                    document.getElementById('resTR').innerText = aiOutput.tr || "-";
                    document.getElementById('resCC').innerText = aiOutput.cc || "-";
                    document.getElementById('resLR').innerText = aiOutput.lr || "-";
                    document.getElementById('resGRA').innerText = aiOutput.gra || "-";
                    
                    document.getElementById('resS1').innerText = "• " + (aiOutput.strength_1 || "");
                    document.getElementById('resS2').innerText = "• " + (aiOutput.strength_2 || "");
                    
                    document.getElementById('resI1').innerHTML = `<span class="text-error font-bold">•</span><span>${{aiOutput.improvement_1 || ""}}</span>`;
                    document.getElementById('resI2').innerHTML = `<span class="text-error font-bold">•</span><span>${{aiOutput.improvement_2 || ""}}</span>`;
                    
                    document.getElementById('resRefinement').innerText = aiOutput.refinement || "";
                    
                    document.getElementById('resVocab').innerHTML = `Instead of "${{aiOutput.vocab_origin || "bad effect"}}", use <span class="text-secondary font-bold">"${{aiOutput.vocab_boost || "detrimental impact"}}"</span>`;
                    document.getElementById('resGrammar').innerHTML = `Correction: <span class="text-red-500 line-through">"${{aiOutput.grammar_origin || ""}}"</span> → <span class="text-secondary font-bold">"${{aiOutput.grammar_fix || ""}}"</span>`;
                    
                    document.getElementById('analysisResult').classList.remove('hidden');
                }}
            }}
        }};

        // 开始精批的逻辑：点击按钮，前端立刻上锁，并将数据传给 Python
        function startAnalysis() {{
            const essay = document.getElementById('essayInput').value.trim();
            const prompt = document.getElementById('promptInput').value.trim();
            const task = document.getElementById('taskSelect').value;

            if (!essay || !prompt) {{
                alert("⚠️ 请确保题目和文章内容都已填写完整！");
                return;
            }}

            if (!apiConfigured) {{
                alert("❌ 密钥未配置，请先在 Streamlit 后台 Settings -> Secrets 中贴入真实的 DeepSeek Key。");
                return;
            }}

            // 1. 本地 UI 立即进入高速加载状态，给用户完美的即时视觉反馈
            document.getElementById('loadingOverlay').classList.remove('hidden');
            document.getElementById('emptyState').classList.add('hidden');
            document.getElementById('analysisResult').classList.add('hidden');

            // 2. 利用 URL Query Parameters 安全高速传输给 Python 拦截器
            const targetUrl = window.parent.location.origin + window.parent.location.pathname + 
                "?task=" + encodeURIComponent(task) + 
                "&prompt=" + encodeURIComponent(prompt) + 
                "&essay=" + encodeURIComponent(essay);
            
            // 触发 parent streamlit 刷新重载
            window.parent.location.href = targetUrl;
        }}

        // 清空重测
        function resetTest() {{
            document.getElementById('essayInput').value = "";
            document.getElementById('promptInput').value = "";
            updateWordCount();
            window.parent.location.href = window.parent.location.origin + window.parent.location.pathname;
        }}

        // 计算单词数
        function updateWordCount() {{
            const text = document.getElementById('essayInput').value.trim();
            const wordCount = text ? text.split(/\\s+/).length : 0;
            document.getElementById('wordCount').innerText = `Word Count: ${{wordCount}} words`;
        }}

        // 一键复制代码
        function copyModelEssay() {{
            const text = document.getElementById('resRefinement').innerText;
            const tempInput = document.createElement("textarea");
            tempInput.value = text;
            document.body.appendChild(tempInput);
            tempInput.select();
            document.execCommand("copy");
            document.body.removeChild(tempInput);
            alert("📋 满分改写范文已成功复制到剪贴板！");
        }}
    </script>
</body>
</html>
"""

# 8. 满屏一键覆盖渲染
st.components.v1.html(HTML_TEMPLATE, height=720, scrolling=False)
