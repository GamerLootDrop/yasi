import streamlit as st
from openai import OpenAI
import json

# 1. 设置 Streamlit 页面基础配置（必须放在最开始）
st.set_page_config(
    page_title="IELTS AI Examiner Pro - Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. 从 Secrets 中读取你的 DeepSeek API 密匙
API_KEY = st.secrets.get("LLM_API_KEY", "")
BASE_URL = st.secrets.get("LLM_BASE_URL", "https://api.deepseek.com/v1") 
MODEL_NAME = st.secrets.get("LLM_MODEL_NAME", "deepseek-chat")

# 初始化临时存储（用来记录是否点击了批改）
if "result_data" not in st.session_state:
    st.session_state.result_data = None
if "loading" not in st.session_state:
    st.session_state.loading = False

# 3. 页面核心逻辑布局
st.markdown("<h2 style='text-align:center; color:#00236f; font-family:Inter; font-weight:800; margin-bottom:10px;'>💡 雅思 AI 尊享版精批系统后台控制中心</h2>", unsafe_allow_html=True)
st.caption("提示：请在下方左侧面板提交作文。系统会通过高速通道调用 DeepSeek 并实时渲染出您刚才提供的那套高定 UI。")

# 建立两栏，左边用来接收用户的真实输入
col_left, col_right = st.columns([1, 1.2], gap="large")

with col_left:
    st.markdown("### 📥 考生输入面板 (Input Block)")
    task_type = st.selectbox(
        "选择你的作文类型 (Task Type)", 
        ["IELTS Academic Task 2 (Essay)", "IELTS Academic Task 1 (Report/Data)", "IELTS General Training Task 1 (Letter)"]
    )
    prompt_input = st.text_area(
        "输入作文题目 (Prompt/Question)", 
        placeholder="Paste the IELTS writing question here...",
        height=100
    )
    essay_input = st.text_area(
        "粘贴你的文章 (Your Essay)", 
        placeholder="Paste your full essay here. Minimum 250 words recommended for Task 2...",
        height=350
    )
    
    submit_btn = st.button("🚀 开始 AI 深度精批 (Run Evaluation)")

# 4. 后端核心大模型拦截与处理
if submit_btn:
    if not essay_input or not prompt_input:
        st.warning("⚠️ 请确保题目和文章内容都已填写完整！")
    elif not API_KEY:
        st.error("❌ 后端大模型未正确配置 API Key，请检查 Secrets。")
    else:
        st.session_state.loading = True
        with st.spinner("⚡ 资深雅思考官正在逐字审核并生成高级渲染报告..."):
            try:
                client = OpenAI(api_key=API_KEY, base_url=BASE_URL)
                
                # 极其严格的格式化 Prompt，强制大模型必须输出符合前端读取的 JSON 数据
                SYSTEM_PROMPT = """Role: Senior IELTS Writing Examiner.
Task: Evaluate the essay strictly based on official band descriptors. 
CRITICAL: You must output ONLY a valid JSON object. Do not include any markdown formatting like ```json or any text outside the JSON.

Expected JSON Structure:
{
  "overall": "7.5",
  "tr": "7.0",
  "cc": "7.5",
  "lr": "8.0",
  "gra": "7.0",
  "level": "Good User (C1 Advanced)",
  "strength_1": "这里写第1个优势亮点...",
  "strength_2": "这里写第2个优势亮点...",
  "improvement_1": "这里写第1个需要改进的点...",
  "improvement_2": "这里写第2个需要改进的点...",
  "refinement": "在这里写下你做出的满分改写长段范文...",
  "vocab_origin": "bad effect",
  "vocab_boost": "detrimental impact",
  "grammar_origin": "The research show",
  "grammar_fix": "shows"
}"""

                USER_CONTENT = f"【Task】: {task_type}\n\n【Prompt】:\n{prompt_input}\n\n【Essay】:\n{essay_input}"
                
                response = client.chat.completions.create(
                    model=MODEL_NAME,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": USER_CONTENT}
                    ],
                    temperature=0.2
                )
                
                # 清洗大模型可能自带的格式小瑕疵
                clean_raw = response.choices[0].message.content.strip()
                if clean_raw.startswith("```json"):
                    clean_raw = clean_raw.split("```json")[1].split("```")[0].strip()
                elif clean_raw.startswith("```"):
                    clean_raw = clean_raw.split("```")[1].split("```")[0].strip()
                    
                st.session_state.result_data = json.loads(clean_raw)
                st.session_state.loading = False
                st.balloons()
            except Exception as e:
                st.error(f"解析或调用发生错误: {str(e)}")
                st.session_state.loading = False

# 5. 把动态数据注入到你的高定 HTML 模板中
with col_right:
    # 默认状态（还没点批改）
    if not st.session_state.result_data:
        html_to_render = """
        <div style="background-color: #f8f9ff; border: 2px dashed #c5c5d3; padding: 100px 20px; text-align: center; border-radius: 12px; font-family: 'Inter', sans-serif;">
            <div style="font-size: 50px; margin-bottom: 20px;">💡</div>
            <h3 style="color: #0b1c30; font-size: 20px; margin: 0 0 10px 0;">等待评估 (Waiting for Input)</h3>
            <p style="color: #444651; font-size: 14px; margin: 0;">在左侧填写好题目和作文，点击“开始 AI 深度精批”，DeepSeek 会瞬间激活右侧的高级看板。</p>
        </div>
        """
    else:
        # 成功拿到 API 数据，开始对你的专属前端页面进行“疯狂魔改填充”
        d = st.session_state.result_data
        
        html_to_render = f"""
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
        <body class="p-2">
            <div class="space-y-4">
                <div class="bg-white border border-slate-200 rounded-xl academic-shadow p-6 flex items-center justify-between">
                    <div>
                        <p class="text-xs text-slate-400 uppercase tracking-wider font-bold">Overall Band Score</p>
                        <h3 class="text-5xl font-black text-[#00236f]">{d.get('overall', '5.5')}</h3>
                        <p class="text-sm text-blue-600 font-bold mt-1">{d.get('level', 'User')}</p>
                    </div>
                    <div class="grid grid-cols-2 gap-3">
                        <div class="bg-slate-50 px-4 py-2 rounded-lg text-center border border-slate-100">
                            <p class="text-[10px] text-slate-400 font-bold">TR</p>
                            <p class="text-lg font-bold text-[#00236f]">{d.get('tr', '5.5')}</p>
                        </div>
                        <div class="bg-slate-50 px-4 py-2 rounded-lg text-center border border-slate-100">
                            <p class="text-[10px] text-slate-400 font-bold">CC</p>
                            <p class="text-lg font-bold text-[#00236f]">{d.get('cc', '5.5')}</p>
                        </div>
                        <div class="bg-slate-50 px-4 py-2 rounded-lg text-center border border-slate-100">
                            <p class="text-[10px] text-slate-400 font-bold">LR</p>
                            <p class="text-lg font-bold text-[#00236f]">{d.get('lr', '5.5')}</p>
                        </div>
                        <div class="bg-slate-50 px-4 py-2 rounded-lg text-center border border-slate-100">
                            <p class="text-[10px] text-slate-400 font-bold">GRA</p>
                            <p class="text-lg font-bold text-[#00236f]">{d.get('gra', '5.5')}</p>
                        </div>
                    </div>
                </div>

                <div class="grid grid-cols-2 gap-4">
                    <div class="bg-white border-l-4 border-l-blue-600 rounded-xl academic-shadow p-4 border border-slate-200">
                        <div class="flex items-center gap-2 mb-3">
                            <span class="material-symbols-outlined text-blue-600 font-bold">verified</span>
                            <span class="text-sm font-bold text-blue-600">优势亮点 (Strengths)</span>
                        </div>
                        <ul class="space-y-2 text-xs text-slate-700">
                            <li class="flex gap-1"><span>•</span><span>{d.get('strength_1', '')}</span></li>
                            <li class="flex gap-1"><span>•</span><span>{d.get('strength_2', '')}</span></li>
                        </ul>
                    </div>
                    <div class="bg-white border-l-4 border-l-red-500 rounded-xl academic-shadow p-4 border border-slate-200">
                        <div class="flex items-center gap-2 mb-3">
                            <span class="material-symbols-outlined text-red-500 font-bold">report</span>
                            <span class="text-sm font-bold text-red-500">改进建议 (Areas for Improvement)</span>
                        </div>
                        <ul class="space-y-2 text-xs text-slate-700">
                            <li class="flex gap-1"><span class="text-red-500">•</span><span>{d.get('improvement_1', '')}</span></li>
                            <li class="flex gap-1"><span class="text-red-500">•</span><span>{d.get('improvement_2', '')}</span></li>
                        </ul>
                    </div>
                </div>

                <div class="bg-white border border-slate-200 rounded-xl academic-shadow p-6">
                    <div class="flex items-center justify-between mb-3">
                        <h4 class="text-md font-bold text-[#00236f]">✨ AI 满分改写建议 (Refinement)</h4>
                    </div>
                    <div class="p-4 bg-slate-50 rounded-lg text-sm italic text-slate-600 border border-slate-100 leading-relaxed whitespace-pre-wrap">
                        "{d.get('refinement', '')}"
                    </div>
                    <div class="mt-4 grid grid-cols-2 gap-4">
                        <div class="p-3 bg-slate-50 rounded border border-slate-100">
                            <p class="text-[10px] text-slate-400 font-bold mb-1 uppercase">Vocabulary Boost</p>
                            <p class="text-xs">Instead of "{d.get('vocab_origin', '')}", use <span class="text-blue-600 font-bold">"{d.get('vocab_boost', '')}"</span></p>
                        </div>
                        <div class="p-3 bg-slate-50 rounded border border-slate-100">
                            <p class="text-[10px] text-slate-400 font-bold mb-1 uppercase">Grammar Fix</p>
                            <p class="text-xs">Correction: <span class="text-red-500 line-through">"{d.get('grammar_origin', '')}"</span> → <span class="text-blue-600 font-bold">"{d.get('grammar_fix', '')}"</span></p>
                        </div>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        
    # 用组件把组装好的精美前端渲染出来（高定 680px 高度自适应滚动）
    st.components.v1.html(html_to_render, height=680, scrolling=True)
