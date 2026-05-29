import streamlit as st
from openai import OpenAI
import json

# 1. 设置 Streamlit 页面基础配置
st.set_page_config(
    page_title="IELTS AI Examiner Pro - Dashboard",
    layout="wide",
    initial_sidebar_state="collapsed" # 隐藏原生侧边栏，全面启用高定前端界面
)

# 2. 从 Secrets 中读取 API 配置
API_KEY = st.secrets.get("LLM_API_KEY", "")
BASE_URL = st.secrets.get("LLM_BASE_URL", "https://api.deepseek.com/v1") 
MODEL_NAME = st.secrets.get("LLM_MODEL_NAME", "deepseek-chat")

# 初始化 session 状态（记录 AI 评估输出数据）
if "ai_output" not in st.session_state:
    st.session_state.ai_output = None

# 安全清洗 JSON 字符串的函数，利用字符转换绕过反引号语法截断
def clean_json_string(raw_str):
    s = raw_str.strip()
    # 动态生成反引号标志 (```)，防止在代码解析中产生歧义
    tb = chr(96) * 3
    if s.startswith(tb):
        lines = s.split("\n")
        if len(lines) > 1:
            lines = lines[1:]  # 去掉首行带 ``` 的标识
        if lines and lines[-1].strip() == tb:
            lines = lines[:-1] # 去掉尾行带 ``` 的标识
        elif lines and lines[-1].endswith(tb):
            lines[-1] = lines[-1][:-3]
        s = "\n".join(lines)
    
    # 再次清理 JSON 头部可能残留的标识
    s = s.strip()
    if s.lower().startswith("json"):
        s = s[4:].strip()
    return s.strip()

# 3. 构造静态与动态混合的高定 HTML 模板
def generate_html(data=None):
    # 默认展示的模拟数据（保证用户未输入前，界面展示也极其丰满、高级）
    overall = data.get("overall", "7.5") if data else "7.5"
    level = data.get("level", "Good User (C1 Advanced)") if data else "Good User (C1 Advanced)"
    tr = data.get("tr", "7.0") if data else "7.0"
    cc = data.get("cc", "7.5") if data else "7.5"
    lr = data.get("lr", "8.0") if data else "8.0"
    gra = data.get("gra", "7.0") if data else "7.0"
    
    s1 = data.get("strength_1", "词汇丰富度极高，使用了大量学术化表达如 'paradigm shift' 和 'prevalent'。") if data else "词汇丰富度极高，使用了大量学术化表达如 'paradigm shift' 和 'prevalent'。"
    s2 = data.get("strength_2", "论点逻辑清晰，通过逻辑连词有效引导了读者的阅读路径。") if data else "论点逻辑清晰，通过逻辑连词有效引导了读者的阅读路径。"
    
    i1 = data.get("improvement_1", "Task Response在第二段论证略显单薄，建议增加具体的现实案例。") if data else "Task Response在第二段论证略显单薄，建议增加具体的现实案例。"
    i2 = data.get("improvement_2", "注意复合句中的标点符号使用，偶尔出现逗号连接句子的错误。") if data else "注意复合句中的标点符号使用，偶尔出现逗号连接句子的错误。"
    
    refinement = data.get("refinement", "While proponents argue that technological advancement serves as a primary catalyst for economic growth, it is imperative to acknowledge the socio-economic disparities it might exacerbate. A balanced approach requires...") if data else "While proponents argue that technological advancement serves as a primary catalyst for economic growth, it is imperative to acknowledge the socio-economic disparities it might exacerbate. A balanced approach requires..."
    
    v_orig = data.get("vocab_origin", "bad effect") if data else "bad effect"
    v_boost = data.get("vocab_boost", "detrimental impact") if data else "detrimental impact"
    g_orig = data.get("grammar_origin", "The research show") if data else "The research show"
    g_fix = data.get("grammar_fix", "shows") if data else "shows"

    # 动态渲染顶层的水印提示
    watermark = "" if data else '<div style="background:#fffbeb; color:#b45309; padding:10px; border-radius:12px; text-align:center; font-size:13px; margin-bottom:12px; font-weight:bold; border: 1px solid #fef3c7;">⚠️ 当前展示为静态高定设计模板，请在下方提交真实作文激活 AI 实时精批报告</div>'

    html_code = f"""
    <!DOCTYPE html>
    <html class="light" lang="en">
    <head>
        <meta charset="utf-8"/>
        <meta content="width=device-width, initial-scale=1.0" name="viewport"/>
        <script src="[https://cdn.tailwindcss.com?plugins=forms,container-queries](https://cdn.tailwindcss.com?plugins=forms,container-queries)"></script>
        <link href="[https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap](https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap)" rel="stylesheet"/>
        <link href="[https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap](https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap)" rel="stylesheet"/>
        <style>
            body {{ font-family: 'Inter', sans-serif; background-color: #f8f9ff; }}
            .academic-shadow {{ box-shadow: 0 4px 6px -1px rgba(30, 58, 138, 0.05); }}
        </style>
    </head>
    <body class="bg-background text-on-background p-4">
        {watermark}
        <div class="flex flex-col lg:flex-row gap-6">
            <!-- Left Sidebar Section -->
            <div class="w-full lg:w-[280px] bg-slate-50 rounded-2xl p-4 flex flex-col gap-4 border border-slate-100 shrink-0">
                <div>
                    <h1 class="text-xl font-black text-[#00236f]">🎓 雅思AI备考中心</h1>
                    <p class="text-xs text-slate-400">Premium v2.5 (商业尊享版)</p>
                </div>
                <div class="bg-blue-50 text-[#00236f] p-4 rounded-xl border border-blue-100">
                    <p class="text-xs font-bold flex items-center gap-1">🎁 独家备考福利</p>
                    <p class="text-[11px] mt-1 opacity-90 leading-relaxed">后台回复 “<b>雅思真题</b>” 即可免费领取 2026 最新雅思考试机经预测及高分词汇表。</p>
                </div>
                <div class="bg-indigo-50 text-indigo-900 p-4 rounded-xl border border-indigo-100">
                    <p class="text-xs font-bold flex items-center gap-1">👥 互助打卡群</p>
                    <p class="text-[11px] mt-1 opacity-90 leading-relaxed">添加学长微信，备注 “<b>作文打卡</b>”，受邀加入千人雅思备考群。</p>
                </div>
                <p class="text-[10px] text-slate-400 border-t pt-2 border-slate-200">⚙️ DeepSeek-V3 Engine Support</p>
            </div>

            <!-- Right Content Area -->
            <div class="flex-1 space-y-4">
                <!-- Header Banner -->
                <div class="border-b pb-2 flex justify-between items-center">
                    <h2 class="text-lg font-bold text-[#00236f]">📊 AI 评估结果报告 (Official Report)</h2>
                </div>

                <!-- Band Score Hero -->
                <div class="bg-white border border-slate-200 rounded-xl academic-shadow p-6 flex items-center justify-between">
                    <div>
                        <p class="text-xs text-slate-400 uppercase tracking-wider font-bold">Overall Band Score</p>
                        <h3 class="text-5xl font-black text-[#00236f]">{overall}</h3>
                        <p class="text-sm text-blue-600 font-bold mt-1">{level}</p>
                    </div>
                    <div class="grid grid-cols-2 gap-3">
                        <div class="bg-slate-50 px-4 py-2 rounded-lg text-center border border-slate-100 min-w-[60px]">
                            <p class="text-[10px] text-slate-400 font-bold">TR</p>
                            <p class="text-md font-bold text-[#00236f]">{tr}</p>
                        </div>
                        <div class="bg-slate-50 px-4 py-2 rounded-lg text-center border border-slate-100 min-w-[60px]">
                            <p class="text-[10px] text-slate-400 font-bold">CC</p>
                            <p class="text-md font-bold text-[#00236f]">{cc}</p>
                        </div>
                        <div class="bg-slate-50 px-4 py-2 rounded-lg text-center border border-slate-100 min-w-[60px]">
                            <p class="text-[10px] text-slate-400 font-bold">LR</p>
                            <p class="text-md font-bold text-[#00236f]">{lr}</p>
                        </div>
                        <div class="bg-slate-50 px-4 py-2 rounded-lg text-center border border-slate-100 min-w-[60px]">
                            <p class="text-[10px] text-slate-400 font-bold">GRA</p>
                            <p class="text-md font-bold text-[#00236f]">{gra}</p>
                        </div>
                    </div>
                </div>

                <!-- Bento Cards -->
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div class="bg-white border-l-4 border-l-blue-600 rounded-xl academic-shadow p-4 border border-slate-200">
                        <p class="text-sm font-bold text-blue-600 mb-2">优势亮点 (Strengths)</p>
                        <ul class="space-y-1.5 text-xs text-slate-600">
                            <li>• {s1}</li>
                            <li>• {s2}</li>
                        </ul>
                    </div>
                    <div class="bg-white border-l-4 border-l-red-500 rounded-xl academic-shadow p-4 border border-slate-200">
                        <p class="text-sm font-bold text-red-500 mb-2">改进建议 (Areas for Improvement)</p>
                        <ul class="space-y-1.5 text-xs text-slate-600">
                            <li>• {i1}</li>
                            <li>• {i2}</li>
                        </ul>
                    </div>
                </div>

                <!-- Model Essay -->
                <div class="bg-white border border-slate-200 rounded-xl academic-shadow p-5">
                    <h4 class="text-sm font-bold text-[#00236f] mb-2">✨ AI 满分改写建议 (Refinement)</h4>
                    <div class="p-4 bg-slate-50 rounded-lg text-xs italic text-slate-600 border border-slate-100 leading-relaxed">
                        "{refinement}"
                    </div>
                    <div class="mt-4 grid grid-cols-1 sm:grid-cols-2 gap-4">
                        <div class="p-3 bg-slate-50 rounded border border-slate-100">
                            <p class="text-[10px] text-slate-400 font-bold uppercase">Vocabulary Boost</p>
                            <p class="text-xs mt-1">Instead of "{v_orig}", use <span class="text-blue-600 font-bold">"{v_boost}"</span></p>
                        </div>
                        <div class="p-3 bg-slate-50 rounded border border-slate-100">
                            <p class="text-[10px] text-slate-400 font-bold uppercase">Grammar Fix</p>
                            <p class="text-xs mt-1">Correction: <span class="text-red-500 line-through">"{g_orig}"</span> → <span class="text-blue-600 font-bold">"{g_fix}"</span></p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    return html_code

# 4. 渲染上方的高定看板
st.components.v1.html(generate_html(st.session_state.ai_output), height=640, scrolling=True)

st.markdown("---")

# 5. 下方控制面板
st.markdown("<h3 style='color:#00236f; font-family:Inter;'>📥 真实作文本系统提交区</h3>", unsafe_allow_html=True)
col_in1, col_in2 = st.columns([1, 2])

with col_in1:
    task_type = st.selectbox("选择作文类型", ["Task 2 (大作文/议论文)", "Task 1 (小作文/图表分析)"])
    submit_btn = st.button("🚀 开始 AI 深度精批")

with col_in2:
    prompt_input = st.text_area("输入作文题目 (Prompt)", placeholder="请在此输入题目...", height=68)
    essay_input = st.text_area("粘贴你的英文文章 (Essay)", placeholder="请在此粘贴文章...", height=150)

# 6. 后端触发
if submit_btn:
    if not essay_input or not prompt_input:
        st.warning("⚠️ 请输入题目和文章！")
    elif "填写你的" in API_KEY or not API_KEY:
        st.error("❌ 密钥配置失效。请在 Streamlit 的 Settings -> Secrets 中贴入真实的 DeepSeek Key。")
    else:
        with st.spinner("⚡ AI 正在精批中..."):
            try:
                client = OpenAI(api_key=API_KEY, base_url=BASE_URL)
                SYSTEM_PROMPT = """You must output ONLY a valid JSON object. Do not include markdown blocks.
Structure:
{
  "overall": "得分", "level": "水平称呼", "tr": "分", "cc": "分", "lr": "分", "gra": "分",
  "strength_1": "亮点1", "strength_2": "亮点2", "improvement_1": "建议1", "improvement_2": "建议2",
  "refinement": "改写范文", "vocab_origin": "原词", "vocab_boost": "好词", "grammar_origin": "错处", "grammar_fix": "对处"
}"""
                response = client.chat.completions.create(
                    model=MODEL_NAME,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": f"题目:{prompt_input}\n文章:{essay_input}"}
                    ],
                    temperature=0.2
                )
                
                raw_content = response.choices[0].message.content
                clean_raw = clean_json_string(raw_content)
                st.session_state.ai_output = json.loads(clean_raw)
                st.rerun() # 立即重载刷新网页，将数据渲染到高定看板
            except Exception as e:
                st.error(f"分析出错，请检查配置: {str(e)}")
