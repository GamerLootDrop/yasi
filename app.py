import streamlit as st
from openai import OpenAI

# 1. 页面基本配置
st.set_page_config(
    page_title="IELTS AI Grader | 雅思AI写作精批",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 自定义高级学术感样式
st.markdown("""
    <style>
    .main .block-container {padding-top: 2rem;}
    .stButton>button {width: 100%; background-color: #1E3A8A; color: white; font-weight: bold;}
    h1 {color: #1E3A8A;}
    </style>
""", unsafe_allow_html=True)

st.title("📝 雅思 AI 写作核心精批系统")
st.caption("基于雅思官方最新公开四维评分标准（TR/CC/LR/GRA）构建")

# 2. 从 Streamlit Secrets 安全读取 API 配置
# 部署后可在 Streamlit 后台的 Settings -> Secrets 里一键配置
API_KEY = st.secrets.get("LLM_API_KEY", "")
BASE_URL = st.secrets.get("LLM_BASE_URL", "https://api.openai.com/v1") 
MODEL_NAME = st.secrets.get("LLM_MODEL_NAME", "gpt-4o")

# 3. 左右分栏布局
col1, col2 = st.columns([1, 1], gap="large")

with col1:
    st.subheader("📥 提交你的作文")
    
    task_type = st.selectbox("选择作文类型", ["Task 1 (小作文/图表分析)", "Task 2 (大作文/议论文)"])
    
    prompt_input = st.text_area(
        "输入作文题目 (Prompt/Question)", 
        placeholder="请在此粘贴雅思写作真题题目，以便 AI 能够精准分析是否跑题...",
        height=100
    )
    
    essay_input = st.text_area(
        "粘贴你的文章 (Your Essay)", 
        placeholder="请在此粘贴你的英文作文，AI 将在数秒内完成考官级全方位精批...",
        height=380
    )
    
    submit_btn = st.button("🚀 开始 AI 深度精批")

with col2:
    st.subheader("📊 AI 评估结果报告")
    
    if submit_btn:
        if not essay_input or not prompt_input:
            st.warning("⚠️ 请确保题目和文章内容都已填写完整！")
        elif not API_KEY:
            st.error("❌ 未检测到后端大模型 API Key。请先在 Streamlit 部署面板的 Secrets 中配置 `LLM_API_KEY`！")
        else:
            with st.spinner("AI 考官正在按照官方标准严厉批改中，请稍候..."):
                try:
                    # 初始化客户端（兼容所有通用OpenAI格式的API）
                    client = OpenAI(api_key=API_KEY, base_url=BASE_URL)
                    
                    # 极其硬核的官方考官调教 Prompt
                    SYSTEM_PROMPT = """Role: You are an official, senior IELTS Writing Examiner with over 15 years of grading experience. 
Task: Evaluate the user's essay strictly according to the official IELTS Band Descriptors for Task 1/Task 2.

Please generate the evaluation report in professional and encouraging Chinese, but keep technical grammar/lexical terms in English. The report must follow this strict Markdown structure:

### 🏆 预估总分 (Estimated Overall Band): [例如: 6.0]

#### 📈 分项评分维度分析 (Criterion Breakdown)
1. **Task Achievement / Response (任务回应情况)**
   - **Score**: [分数]
   - **诊断**: [指出切题程度、论点是否充分展开、小作文是否概括了核心趋势]
2. **Coherence and Cohesion (连贯与衔接)**
   - **Score**: [分数]
   - **诊断**: [指出段落分层、逻辑连接词的使用是否自然或过度、指代词是否准确]
3. **Lexical Resource (词汇丰富程度)**
   - **Score**: [分数]
   - **诊断**: [指出词汇重复问题、搭配错误，或表扬亮点学术词汇]
4. **Grammatical Range and Accuracy (语法多样性与准确性)**
   - **Score**: [分数]
   - **诊断**: [指出时态、主谓一致等硬伤，以及复合句型的使用比例]

---

### 🔍 逐句硬伤修正 (Sentence-by-Sentence Corrections)
(Please list the top 3-5 critical errors in the original essay, format as follows:)
- **❌ 原文**: "..."
- **🔧 修正**: "..."
- **💡 考官解析**: [用中文简明扼要解释为什么错，或者怎么写更好]

---

### ✨ 官方推荐高分升级范文 (Band 7.5+ Model Essay)
[基于用户的原意和题目，由你重写一篇 7.5-8.0 分水平的示范文章，并将使用的【高级词汇/高分句型】用**加粗**表示。]"""

                    USER_CONTENT = f"【作文类型】: {task_type}\n\n【题目】:\n{prompt_input}\n\n【学生作文】:\n{essay_input}"
                    
                    # 调用大模型
                    response = client.chat.completions.create(
                        model=MODEL_NAME,
                        messages=[
                            {"role": "system", "content": SYSTEM_PROMPT},
                            {"role": "user", "content": USER_CONTENT}
                        ],
                        temperature=0.3
                    )
                    
                    result_text = response.choices[0].message.content
                    
                    # 用美观的 Markdown 渲染出来的批改报告
                    st.success("🎉 精批报告生成完毕！")
                    st.markdown(result_text)
                        
                except Exception as e:
                    st.error(f"调用 API 时发生错误: {str(e)}")
    else:
        st.info("💡 在左侧输入作文并点击按钮后，这里将实时生成雅思考官级别的精批报告。")