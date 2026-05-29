import streamlit as st
from openai import OpenAI

# 1. 页面高级配置
st.set_page_config(
    page_title="IELTS AI Examiner | 雅思AI官方标准精批系统",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 注入国际化高定 CSS
st.markdown("""
    <style>
    .main { background: linear-gradient(135deg, #F8FAFC 0%, #F1F5F9 100%); }
    .main-title { color: #1E3A8A; font-size: 2.3rem; font-weight: 800; letter-spacing: -0.05em; }
    .stButton>button {
        width: 100%;
        background: linear-gradient(90deg, #1E3A8A 0%, #2563EB 100%);
        color: white !important; border: none; padding: 0.75rem; border-radius: 12px; font-weight: 700;
        box-shadow: 0 4px 6px -1px rgba(37, 99, 235, 0.2);
    }
    .community-box { background: linear-gradient(135deg, #EFF6FF 0%, #DBEAFE 100%); padding: 1.2rem; border-radius: 12px; border: 1px solid #BFDBFE; margin-top: 1rem; }
    </style>
""", unsafe_allow_html=True)

# 2. API 配置读取
API_KEY = st.secrets.get("LLM_API_KEY", "")
BASE_URL = st.secrets.get("LLM_BASE_URL", "https://api.deepseek.com/v1") 
MODEL_NAME = st.secrets.get("LLM_MODEL_NAME", "deepseek-chat")

# 3. 侧边栏：中文引流矩阵
with st.sidebar:
    st.markdown("### 🎓 雅思AI备考中心")
    st.markdown("💬 **Current Version**: Premium v2.5")
    st.markdown("---")
    st.markdown("""
    <div class="community-box">
        <h4 style="margin-top:0;color:#1E40AF;">🎁 🎯 领取今日备考福利</h4>
        <p style="font-size:0.85rem;color:#1E3A8A;margin-bottom:0.5rem;">添加助教微信，暗号 <b>“AI精批”</b>，免费领取 2026 最新雅思全套机经及高分口语题库！</p>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("---")
    st.caption("⚡ Powered by DeepSeek-V3 Engine")

# 4. 主页面布局（左边英文/双语专业操作，右边出报告）
st.markdown('<h1 class="main-title">📝 IELTS AI Writing Examiner</h1>', unsafe_allow_html=True)
st.markdown('<p style="color:#64748B; font-size:1rem; margin-bottom:2rem;">Official Band Descriptors Alignment System (TR / CC / LR / GRA)</p>', unsafe_allow_html=True)

col1, col2 = st.columns([1, 1], gap="large")

with col1:
    st.markdown("### 📥 Submission Panel")
    
    # 选项做成国际范的双语
    task_type = st.selectbox(
        "Select Task Type (选择作文类型)", 
        ["Task 2 (大作文/议论文)", "Task 1 (小作文/图表分析)"]
    )
    
    prompt_input = st.text_area(
        "📌 Writing Prompt / Question (输入作文题目)", 
        placeholder="Paste the IELTS writing question here...",
        height=100
    )
    
    essay_input = st.text_area(
        "✍️ Your Essay (粘贴你的文章)", 
        placeholder="Paste your full essay here. AI will evaluate it in seconds...",
        height=380
    )
    
    submit_btn = st.button("🚀 Start AI Deep Evaluation")

with col2:
    st.markdown("### 📊 Evaluation Report")
    
    if submit_btn:
        if not essay_input or not prompt_input:
            st.warning("⚠️ Please complete both the prompt and essay fields before submission!")
        elif not API_KEY:
            st.error("❌ API Configuration Error.")
        else:
            with st.spinner("⚡ Official Examiner is evaluating your essay... Please wait."):
                try:
                    client = OpenAI(api_key=API_KEY, base_url=BASE_URL)
                    
                    # 强行规范输出格式，让大模型输出带有卡片高级感的 Markdown
                    SYSTEM_PROMPT = """Role: Senior IELTS Writing Examiner.
Task: Evaluate the essay strictly based on official band descriptors. 
Language: Use English for scores and official criteria names, but write all diagnostic feedback and explanations in professional Chinese so the student can perfectly understand their mistakes.

Format requirements:
### 🏆 Estimated Overall Band: [Score]

#### 📈 Criterion Breakdown
1. **Task Achievement / Response** - **Score**: [Score]
   - **诊断**: [Chinese Feedback]
2. **Coherence and Cohesion**
   - **Score**: [Score]
   - **诊断**: [Chinese Feedback]
3. **Lexical Resource**
   - **Score**: [Score]
   - **诊断**: [Chinese Feedback]
4. **Grammatical Range and Accuracy**
   - **Score**: [Score]
   - **诊断**: [Chinese Feedback]

---
### 🔍 Sentence-by-Sentence Corrections (逐句硬伤修正)
- ❌ **Original**: "..."
- 🔧 **Correction**: "..."
- 💡 **Analysis**: [Chinese Explanation]

---
### ✨ Band 7.5+ Model Essay (高分示范范文)
[Generate a high-quality model essay based on user's content. Bold the high-advanced vocabulary and structures.]"""

                    USER_CONTENT = f"【Task】: {task_type}\n\n【Prompt】:\n{prompt_input}\n\n【Essay】:\n{essay_input}"
                    
                    response = client.chat.completions.create(
                        model=MODEL_NAME,
                        messages=[
                            {"role": "system", "content": SYSTEM_PROMPT},
                            {"role": "user", "content": USER_CONTENT}
                        ],
                        temperature=0.3
                    )
                    
                    st.balloons()
                    st.markdown(response.choices[0].message.content)
                        
                except Exception as e:
                    st.error(f"Error: {str(e)}")
    else:
        st.markdown("""
        <div style="background-color: #FFFFFF; padding: 2.5rem; border-radius: 16px; border: 2px dashed #CBD5E1; text-align: center; margin-top: 1rem;">
            <p style="color: #64748B; font-size: 1rem; margin-bottom: 0;">💡 Submit your prompt and essay on the left, then click the button to generate an official examiner-level report here.</p>
        </div>
        """, unsafe_allow_html=True)
