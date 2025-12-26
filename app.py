"""
PDF2PDF Prototype - High-Fidelity UI Mockup
A Streamlit-based demonstration of the "Chat & Modify" workflow.
OPTIMIZED FOR: Compact single-screen layout & Reliable PDF Display
FINAL TUNING: Optimized Column Ratios [5, 5, 2] to fit MacBook Air screens better
"""
import streamlit as st
import os
from streamlit_pdf_viewer import pdf_viewer
from models import JobConfig, ChatMessage, GlossaryType, LayoutPriority
from backend_mock import (
    mock_parse_pdf,
    mock_process_chat_command,
    get_sample_chat_history
)

# Page configuration
st.set_page_config(
    page_title="PDF2PDF",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# MANDATORY CSS: Compact Layout
st.markdown("""
<style>
    /* Global Layout Fixes */
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 0rem !important;
        max-width: 98% !important;
    }
    h1, h2, h3, h4 {
        margin-top: 0rem !important;
        margin-bottom: 0.5rem !important;
    }
    .element-container { margin-bottom: 0.5rem !important; }
    div[data-testid="stFileUploader"] { margin: auto; width: 80%; }
    
    /* Header Style */
    .main-header {
        text-align: center;
        padding: 0.5rem 0;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 8px;
        margin-bottom: 0.5rem;
    }
    .main-header h1 { font-size: 1.5rem; margin: 0 !important; }
    
    /* Step Indicator */
    .step-indicator {
        text-align: center;
        padding: 0.3rem;
        margin-bottom: 0.5rem;
        background-color: #f0f2f6;
        border-radius: 6px;
        font-size: 0.9rem;
    }
    
    /* Chat & Compact UI */
    .stChatMessage { padding: 0.5rem; }
    .stButton button { width: 100%; }
</style>
""", unsafe_allow_html=True)

# Session State Init
if "step" not in st.session_state: st.session_state.step = 1
if "uploaded_file" not in st.session_state: st.session_state.uploaded_file = None
if "config" not in st.session_state: st.session_state.config = None
if "result" not in st.session_state: st.session_state.result = None
if "chat_history" not in st.session_state: st.session_state.chat_history = []

def render_header():
    st.markdown("""
    <div class="main-header">
        <h1>📄 PDF2PDF</h1>
    </div>
    """, unsafe_allow_html=True)

def render_step_indicator(current_step: int):
    steps = ["Upload", "Configure", "Workspace"]
    html = "<div class='step-indicator'><b>" + " → ".join(
        [f"<span style='color: {'#667eea' if i==current_step else '#ccc'}'>{s}</span>" for i, s in enumerate(steps, 1)]
    ) + "</b></div>"
    st.markdown(html, unsafe_allow_html=True)

# --- HELPER FUNCTION: Display PDF with streamlit-pdf-viewer ---
def display_pdf(file_path, height=700):
    """
    使用 streamlit-pdf-viewer 显示 PDF。
    这是经过验证最稳定的方法。
    """
    if not os.path.exists(file_path):
        st.error(f"📄 File not found: {file_path}")
        return

    try:
        with open(file_path, "rb") as f:
            pdf_bytes = f.read()
        
        # 維持 width=700，配合下方調整過的欄位比例，可以更輕鬆放入螢幕
        pdf_viewer(pdf_bytes, width=700, height=height)
    except Exception as e:
        st.error(f"Error loading PDF: {str(e)}")

# --- STEPS ---

def step1_upload():
    render_step_indicator(1)
    st.markdown("#### 📤 Upload Document")
    
    demo_file = "somatosensory.pdf"
    has_demo = os.path.exists(demo_file)
    
    uploaded = st.file_uploader("Upload PDF", type=["pdf"], label_visibility="collapsed")
    
    if uploaded:
        st.session_state.uploaded_file = uploaded
        st.success(f"Loaded: {uploaded.name}")
        if st.button("Continue →", type="primary"):
            st.session_state.step = 2
            st.rerun()
    elif has_demo:
        class MockFile: name = demo_file
        if st.button(f"👉 Use Demo File ({demo_file})"):
            st.session_state.uploaded_file = MockFile()
            st.session_state.step = 2
            st.rerun()

def step2_configuration():
    render_step_indicator(2)
    st.markdown(f"#### ⚙️ Configure • {st.session_state.uploaded_file.name}")
    
    with st.form("conf"):
        c1, c2 = st.columns(2)
        with c1:
            lang = st.selectbox("Target Language", ["Chinese (Traditional - HK)", "English"])
            glossary = st.selectbox("Glossary", [g.value for g in GlossaryType])
        with c2:
            prio = st.radio("Layout Priority", [p.value.title() for p in LayoutPriority], horizontal=True)
        
        c_Back, c_Go = st.columns([1, 2])
        with c_Back:
            if st.form_submit_button("← Back"):
                st.session_state.step = 1
                st.rerun()
        with c_Go:
            if st.form_submit_button("Start Processing 🚀", type="primary"):
                st.session_state.config = JobConfig(
                    target_language=lang,
                    glossary=GlossaryType(glossary),
                    layout_priority=LayoutPriority(prio.lower()),
                    source_filename=st.session_state.uploaded_file.name
                )
                st.session_state.step = 3
                st.rerun()

def step3_workspace():
    render_step_indicator(3)
    
    if not st.session_state.result:
        with st.spinner("Agents working..."):
            st.session_state.result = mock_parse_pdf(st.session_state.uploaded_file.name, st.session_state.config)
            st.session_state.chat_history = get_sample_chat_history()
        st.rerun()

    input_path = "somatosensory.pdf"
    output_path = "output_tc.pdf"
    
    # Fallback Mechanism
    if not os.path.exists(output_path):
        if os.path.exists(input_path):
            output_path = input_path
            st.toast("⚠️ Output missing, showing original as placeholder.")
        else:
            st.error("❌ Missing demo files! Please ensure 'somatosensory.pdf' is in the folder.")
            return

    st.markdown(f"**Workspace**: {st.session_state.config.source_filename} → {st.session_state.config.target_language}")

    # 🟢 黃金比例修正：[5, 5, 2]
    # 這會顯著壓縮最右側的 Chat 欄位，將寶貴的螢幕寬度留給 PDF。
    # 這能讓您在不需要縮小到 50% 的情況下，也能看清楚內容。
    col_L, col_R, col_Chat = st.columns([5, 5, 2])
    
    height_px = 700
    
    with col_L:
        st.markdown("###### 📄 Original")
        display_pdf(input_path, height=height_px)

    with col_R:
        st.markdown("###### 🌍 Translated (zh-HK)")
        display_pdf(output_path, height=height_px)

    with col_Chat:
        st.markdown("###### 🤖 Assistant")
        with st.container(height=height_px - 60):
            for msg in st.session_state.chat_history:
                with st.chat_message(msg.role):
                    st.markdown(msg.content)
        
        prompt = st.chat_input("Modify layout...")
        if prompt:
            st.session_state.chat_history.append(ChatMessage(role="user", content=prompt))
            with st.spinner("Fixing..."):
                resp, _ = mock_process_chat_command(prompt, st.session_state.result.blocks)
                st.session_state.chat_history.append(ChatMessage(role="assistant", content=resp))
            st.rerun()

    # Footer
    c1, c2, c3 = st.columns(3)
    if c1.button("💾 Export"): st.success("Exported!")
    if c2.button("📊 Report"): st.info("Report Generated")
    if c3.button("🔄 Reset"):
        st.session_state.step = 1
        st.session_state.result = None
        st.rerun()

def main():
    render_header()
    if st.session_state.step == 1: step1_upload()
    elif st.session_state.step == 2: step2_configuration()
    elif st.session_state.step == 3: step3_workspace()

if __name__ == "__main__":
    main()
