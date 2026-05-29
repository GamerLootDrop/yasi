import streamlit as st
from openai import OpenAI

# 1. 页面高级配置与主题定制
st.set_page_config(
    page_title="IELTS AI Examiner Premium | 雅思AI尊享版精批系统",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 注入高定 CSS 样式（渐变背景、精致卡片、现代字体）
st.markdown("""
    <style>
    /* 全局背景与字体 */
    .main {
        background: linear-gradient(135deg, #F8FAFC 0%, #F1F5F9 100%);
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }
    /* 标题样式 */
    .main-title {
        color: #1E3A8A;
        font-size: 2.5rem;
        font-weight: 800;
        letter-spacing: -0.05em;
        margin-bottom: 0.5rem;
    }
    /* 侧边栏样式 */
    .sidebar .sidebar-content {
        background-color: #FFFFFF;
    }
    /* 按钮高级样式 */
    .stButton>button {
        width: 100%;
        background: linear-gradient(90deg, #1E3A8A 0%, #2563EB 100%);
        color: white !important;
        border: none;
        padding: 0.75rem;
        border-radius: 12px;
        font-weight: 700;
        font-size: 1.1rem;
        box-shadow: 0 4px 6px -1px rgba(37, 99, 235, 0.2);
        transition: all 0.2s;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 15px -3px rgba(37, 99, 235, 0.3);
    }
    /* 结果分析卡片 */
    .criterion-card {
        background-color: #FFFFFF;
        padding: 1.5rem;
        border-radius: 16px;
        border-left: 6px solid #2563EB;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        margin-bottom: 1rem;
    }
    .score-badge {
        background-color: #EFF6FF;
        color: #1E40AF;
        padding: 0.25rem 0.75rem;
        border-radius: 9999px;
        font-weight: 700;
        float: right;
    }
    /* 引流卡片 */
    .community-box {
        background: linear-gradient(135deg, #EFF6FF 0%, #DBEAFE 100%);
        padding: 1.2rem;
        border-radius: 12px;
        border: 1px solid #BFDBFE;
        margin-top: 1rem;
    }
    </style>
""", unsafe_allow_html=True)

# 2. 从 Streamlit Secrets 安全读取 API 配置
API_KEY = st.secrets.get("LLM_API_KEY", "")
BASE_URL = st.secrets.get("LLM_BASE_URL", "https://api.deepseek.com/v1") 
MODEL_NAME = st.secrets.get("LLM_MODEL_NAME", "deepseek-chat")

# 3. 侧边栏：自媒体商业引流矩阵（功能多点）
with st.sidebar:
    st.markdown("### 🎓 雅思AI备考中心")
    st.markdown("💬 **版本号**: Premium v2.1 (商业测试版)")
    st.markdown("---")
    
    # 引流模块 1
    st.markdown("""
    <div class="community-box">
        <h4 style="margin-top:0;color:#1E40AF;">🎁 独家备考福利</h4>
        <p style="font-size:0.85rem;color:#1E3A8A;margin-bottom:0.5rem;">后台回复 <b>“雅思真题”</b> 即可免费领取 2026 最新雅思考试机经预测及高分词汇表。</p>
    </div>
    """, unsafe_allow_html=True)
    
    # 引流模块 2
    st.markdown("""
    <div class="community-box" style="background:linear-gradient(135deg, #F0FDF4 0%, #DCFCE7 100%); border: 1px solid #BBF7D0;">
        <h4 style="margin-top:0;color:#166534;">👥 互助打卡群</h4>
        <p style="font-size:0.85rem;color:#14532D;margin-bottom:0;">添加学长微信，备注 <b>“作文打卡”</b>，受邀加入千人雅思备考群，每日分享7.5分地道表达。</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    st.caption("⚙️ 后端技术支持: DeepSeek-V3 高速安全通道")

# 4. 主页面布局
st.markdown('<h1 class="main-title">📝 IELTS AI Examiner Pro</h1>', unsafe_allow_html=True)
st.markdown('<p style="color:#64748B; font-size:1.1rem; margin-bottom:2rem;">基于最新雅思官方四维标准（TR/CC/LR/GRA）的考官级精批系统</p>', unsafe_allow_html=True)

col1, col2 = st.columns([1, 1], gap="large")

with col1:
    st.markdown("### 📥 提交作文本系统")
    
    task_type = st.selectbox("📝 选择你的作文类型 (Task Type)", ["Task 2 (大作文/议论文)", "Task 1 (小作文/图表分析)"])
    
    prompt_input = st.text_area(
        "📌 输入作文题目 (Prompt/Question)", 
        placeholder="请粘贴雅思写作真题题目...",
        height=100
    )
    
    essay_input = st.text_area(
        "✍️ 粘贴你的文章 (Your Essay)", 
        placeholder="请在此粘贴你的英文作文...",
        height=380
    )
    
    submit_btn = st.button("🚀 开始 AI 深度精批")

with col2:
    st.markdown("### 📊 AI 评估结果报告")
    
    if submit_btn:
        if not essay_input or not prompt_input:
            st.warning("⚠️ 请确保题目和文章内容都已填写完整！")
        elif not API_KEY:
            st.error("❌ 后端大模型未正确配置 API Key！")
        else:
            with st.spinner("⚡ AI 考官正在用官方扣分标准逐字审核中..."):
                try:
                    client = OpenAI(api_key=API_KEY, base_url=BASE_URL)
                    
                    SYSTEM_PROMPT = """Role: You are an official, senior IELTS Writing Examiner with over 15 years of grading experience. 
Task: Evaluate the user's essay strictly according to the official IELTS Band Descriptors for Task 1/Task 2.
Format requirement: Output beautifully using Markdown. Add clean spacing."""

                    USER_CONTENT = f"【作文类型】: {task_type}\n\n【题目】:\n{prompt_input}\n\n【学生作文】:\n{essay_input}"
                    
                    response = client.chat.completions.create(
                        model=MODEL_NAME,
                        messages=[
                            {"role": "system", "content": SYSTEM_PROMPT},
                            {"role": "user", "content": USER_CONTENT}
                        ],
                        temperature=0.3
                    )
                    
                    result_text = response.choices[0].message.content
                    st.balloons() # 增加成功特效
                    st.markdown(result_text)
                        
                except Exception as e:
                    st.error(f"调用 API 时发生错误: {str(e)}")
    else:
        st.markdown("""
        <div style="background-color: #FFFFFF; padding: 2.5rem; border-radius: 16px; border: 2px dashed #CBD5E1; text-align: center; margin-top: 1rem;">
            <p style="color: #64748B; font-size: 1.1rem; margin-bottom: 0;">💡 在左侧填写好题目和作文，点击“开始 AI 深度精批”，5秒内为您呈献满分改写与四维诊断报告。</p>
        </div>
        """, unsafe_allow_html=True)
