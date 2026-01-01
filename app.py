"""
PDF2PDF Prototype - High-Fidelity UI Mockup
A Streamlit-based demonstration of the "Chat & Modify" workflow.
OPTIMIZED FOR: Compact single-screen layout & Reliable PDF Display
PDF RENDERING: Smart Hybrid (base64 <2MB, PyMuPDF images ≥2MB)
"""
import streamlit as st
import os
import base64
from dotenv import load_dotenv
import fitz  # PyMuPDF - for PDF to image conversion
from models import JobConfig, ChatMessage, GlossaryType, LayoutPriority, ProcessResult
from backend_wrapper import run_pipeline_subprocess
from backend_mock import get_sample_chat_history, mock_process_chat_command

# Load environment variables (API key)
load_dotenv()

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
    
    /* PDF Iframe Styling */
    .pdf-container {
        border: 1px solid #ddd;
        border-radius: 4px;
        overflow: hidden;
    }
    
    /* Hide end div */
    div#end {
        display: none !important;
    }
</style>
""", unsafe_allow_html=True)

# Session State Init
if "step" not in st.session_state:
    st.session_state.step = "upload"
if "uploaded_file" not in st.session_state:
    st.session_state.uploaded_file = None
if "config" not in st.session_state:
    st.session_state.config = None
if "result" not in st.session_state:
    st.session_state.result = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []


def render_header():
    """Render the main header"""
    st.markdown("""
    <div class="main-header">
        <h1>📄 PDF2PDF</h1>
    </div>
    """, unsafe_allow_html=True)


def render_step_indicator(current_step: str):
    """Render step indicator with highlighting"""
    steps = ["upload", "configure", "workspace"]
    labels = ["Upload", "Configure", "Workspace"]
    
    step_html = []
    for step, label in zip(steps, labels):
        color = "#667eea" if step == current_step else "#ccc"
        step_html.append(f"<span style='color: {color}'>{label}</span>")
    
    html = f"<div class='step-indicator'><b>{' → '.join(step_html)}</b></div>"
    st.markdown(html, unsafe_allow_html=True)


def display_pdf(file_path: str, height: int = 700, show_download: bool = False):
    """
    Smart Hybrid PDF Display:
    - Small files (<2MB): Use base64 embed (fast, interactive)
    - Large files (≥2MB): Convert to images using PyMuPDF (bypasses browser limits)
    
    Args:
        file_path: Path to the PDF file
        height: Height of the viewer in pixels
        show_download: Whether to show a download button below the PDF
    
    Returns:
        bool: True if successful, False otherwise
    """
    # Convert to absolute path
    file_path = os.path.abspath(file_path)
    
    # Verify file exists
    if not os.path.exists(file_path):
        st.error(f"📄 File not found: {file_path}")
        return False
    
    # Get file size
    file_size = os.path.getsize(file_path)
    file_size_mb = file_size / (1024 * 1024)
    
    if file_size == 0:
        st.error(f"⚠️ File is empty (0 bytes): {file_path}")
        return False
    
    try:
        # Read PDF bytes
        with open(file_path, "rb") as f:
            pdf_bytes = f.read()
        
        # STRATEGY 1: Small files (<2MB) - Use base64 embed
        if file_size_mb < 2.0:
            st.caption(f"📄 {file_size_mb:.2f} MB - Using interactive PDF viewer")
            base64_pdf = base64.b64encode(pdf_bytes).decode('utf-8')
            pdf_html = f"""
                <iframe 
                    src="data:application/pdf;base64,{base64_pdf}#toolbar=0&navpanes=0&scrollbar=0" 
                    type="application/pdf" 
                    width="100%" 
                    height="{height}px"
                    style="border: 1px solid #ddd; border-radius: 4px;"
                ></iframe>
            """
            st.markdown(pdf_html, unsafe_allow_html=True)
        
        # STRATEGY 2: Large files (≥2MB) - Convert to images
        else:
            st.caption(f"📄 {file_size_mb:.2f} MB - Using image rendering (first 5 pages)")
            
            # Open PDF with PyMuPDF
            pdf_doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            
            # Create scrollable container
            with st.container(height=height):
                # Render first 5 pages
                max_pages = min(5, len(pdf_doc))
                for page_num in range(max_pages):
                    page = pdf_doc[page_num]
                    
                    # Render at 2x resolution for quality
                    pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
                    img_bytes = pix.tobytes("png")
                    
                    # Display as image
                    st.image(img_bytes, caption=f"Page {page_num + 1}")
                
                # Show pagination info
                if len(pdf_doc) > max_pages:
                    st.info(f"📄 Showing first {max_pages} of {len(pdf_doc)} pages")
            
            pdf_doc.close()
        
        # Show download button if requested
        if show_download:
            filename = os.path.basename(file_path)
            st.download_button(
                label=f"⬇️ Download {filename}",
                data=pdf_bytes,
                file_name=filename,
                mime="application/pdf"
            )
        
        return True
        
    except Exception as e:
        st.error(f"❌ Error loading PDF: {str(e)}")
        st.caption(f"File path: {file_path}")
        st.caption(f"File size: {file_size:,} bytes ({file_size_mb:.1f} MB)")
        
        # Fallback download button
        if 'pdf_bytes' in locals():
            st.download_button(
                label=f"📥 Download {os.path.basename(file_path)}",
                data=pdf_bytes,
                file_name=os.path.basename(file_path),
                mime="application/pdf"
            )
        return False


# --- STEP 1: UPLOAD ---
def step1_upload():
    """Step 1: File Upload Interface"""
    render_step_indicator("upload")
    st.markdown("#### 📤 Upload Document")
    
    # Check for demo file
    demo_file = "somatosensory.pdf"
    has_demo = os.path.exists(demo_file)
    
    # File uploader
    uploaded = st.file_uploader(
        "Upload PDF",
        type=["pdf"],
        label_visibility="collapsed"
    )
    
    if uploaded:
        # Check if this is a new file (different from previous upload)
        if (st.session_state.uploaded_file is None or 
            uploaded.name != st.session_state.uploaded_file.name):
            # Clear previous results when uploading a new file
            st.session_state.result = None
            st.session_state.chat_history = []
            st.session_state.config = None
        
        st.session_state.uploaded_file = uploaded
        st.success(f"✅ Loaded: {uploaded.name}")
        if st.button("Continue →", type="primary"):
            st.session_state.step = "configure"
            st.rerun()
    elif has_demo:
        st.info(f"💡 Demo file available: `{demo_file}`")
        if st.button(f"👉 Use Demo File ({demo_file})", type="secondary"):
            # Create a mock file object
            class MockFile:
                name = demo_file
            # Clear previous results when loading demo file
            st.session_state.result = None
            st.session_state.chat_history = []
            st.session_state.config = None
            st.session_state.uploaded_file = MockFile()
            st.session_state.step = "configure"
            st.rerun()


# --- STEP 2: CONFIGURE ---
def step2_configuration():
    """Step 2: Translation Configuration"""
    render_step_indicator("configure")
    st.markdown(f"#### ⚙️ Configure Translation • {st.session_state.uploaded_file.name}")
    
    with st.form("config_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            target_language = st.selectbox(
                "Target Language",
                ["Chinese (Traditional - HK)", "English", "Spanish", "French", "German"],
                index=0
            )
            glossary = st.selectbox(
                "Glossary",
                [g.value for g in GlossaryType]
            )
        
        with col2:
            layout_priority = st.radio(
                "Layout Priority",
                [p.value.title() for p in LayoutPriority],
                horizontal=True
            )
        
        # Form buttons
        col_back, col_start = st.columns([1, 2])
        with col_back:
            back_button = st.form_submit_button("← Back")
        with col_start:
            start_button = st.form_submit_button("Start Processing 🚀", type="primary")
        
        if back_button:
            st.session_state.step = "upload"
            st.rerun()
        
        if start_button:
            # Save configuration
            st.session_state.config = JobConfig(
                target_language=target_language,
                glossary=GlossaryType(glossary),
                layout_priority=LayoutPriority(layout_priority.lower()),
                source_filename=st.session_state.uploaded_file.name
            )
            st.session_state.step = "workspace"
            st.rerun()


# --- STEP 3: WORKSPACE ---
def step3_workspace():
    """Step 3: Interactive Workspace with Split View"""
    render_step_indicator("workspace")
    
    # Process the PDF if not already done
    if not st.session_state.result:
        # Check for API key
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            st.error("❌ OPENROUTER_API_KEY not found in .env file!")
            if st.button("← Back to Configure"):
                st.session_state.step = "configure"
                st.rerun()
            return
        
        with st.spinner("🤖 AI Translation in progress... (This may take several minutes)"):
            try:
                # Determine input path - always use absolute paths
                if hasattr(st.session_state.uploaded_file, 'read'):
                    # Streamlit uploaded file - save to temp location with absolute path
                    temp_input = os.path.abspath("temp_upload.pdf")
                    with open(temp_input, "wb") as f:
                        f.write(st.session_state.uploaded_file.getbuffer())
                    input_file = temp_input
                else:
                    # File path (demo file) - ensure absolute path
                    input_file = os.path.abspath(st.session_state.uploaded_file.name)
                
                # Run real translation pipeline
                output_pdf = run_pipeline_subprocess(input_file, api_key)
                
                st.session_state.result = ProcessResult(
                    original_pdf_path=input_file,
                    translated_pdf_path=output_pdf,
                    status="completed"
                )
                st.session_state.chat_history = get_sample_chat_history()
                st.success("✅ Translation completed!")
                
            except Exception as e:
                st.error(f"❌ Translation failed: {str(e)}")
                if st.button("← Back to Configure"):
                    st.session_state.step = "configure"
                    st.rerun()
                return
        st.rerun()
    
    # Define file paths from actual translation result
    input_path = st.session_state.result.original_pdf_path
    output_path = st.session_state.result.translated_pdf_path or "translated_output.pdf"
    
    # Verify files exist
    if not os.path.exists(input_path):
        st.error(f"❌ Original PDF not found: {input_path}")
        return
    
    if not os.path.exists(output_path):
        st.warning("⚠️ Translated PDF not found, showing original as placeholder.")
        output_path = input_path
    
    # Workspace header
    st.markdown(
        f"**Workspace**: {st.session_state.config.source_filename} "
        f"→ {st.session_state.config.target_language}"
    )
    
    # Three-column layout: Original PDF | Translated PDF | Chat
    col_original, col_translated, col_chat = st.columns([5, 5, 2])
    
    pdf_height = 700
    
    # Left Column: Original PDF
    with col_original:
        st.markdown("###### 📄 Original")
        
        # Debug info
        with st.expander("🔍 Debug Info", expanded=False):
            st.write(f"Path: `{input_path}`")
            st.write(f"Exists: {os.path.exists(input_path)}")
            if os.path.exists(input_path):
                st.write(f"Size: {os.path.getsize(input_path):,} bytes")
        
        display_pdf(input_path, height=pdf_height, show_download=False)
    
    # Middle Column: Translated PDF
    with col_translated:
        st.markdown("###### 🌍 Translated (zh-HK)")
        
        # Debug info
        with st.expander("🔍 Debug Info", expanded=False):
            st.write(f"Path: `{output_path}`")
            st.write(f"Exists: {os.path.exists(output_path)}")
            if os.path.exists(output_path):
                st.write(f"Size: {os.path.getsize(output_path):,} bytes")
        
        # Enhanced verification before display
        if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            success = display_pdf(output_path, height=pdf_height, show_download=True)
            if not success:
                st.warning("⚠️ Unable to render translated PDF. Please check the download button above.")
        else:
            st.warning("⚠️ Translated PDF not yet available")
            if output_path:
                st.caption(f"Expected path: {output_path}")
                st.caption(f"Exists: {os.path.exists(output_path)}")
                if os.path.exists(output_path):
                    st.caption(f"Size: {os.path.getsize(output_path)} bytes")
    
    # Right Column: AI Assistant Chat
    with col_chat:
        st.markdown("###### 🤖 Assistant")
        
        # Chat message container with fixed height
        with st.container(height=pdf_height - 60):
            for msg in st.session_state.chat_history:
                with st.chat_message(msg.role):
                    st.markdown(msg.content)
        
        # Chat input
        prompt = st.chat_input("Ask or modify layout...")
        if prompt:
            # Add user message
            st.session_state.chat_history.append(
                ChatMessage(role="user", content=prompt)
            )
            
            # Process and get response
            with st.spinner("🤖 Processing..."):
                response, _ = mock_process_chat_command(
                    prompt,
                    st.session_state.result.blocks
                )
                st.session_state.chat_history.append(
                    ChatMessage(role="assistant", content=response)
                )
            st.rerun()
    
    # Footer actions
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("💾 Export Final PDF"):
            st.success("✅ PDF exported successfully!")
    
    with col2:
        if st.button("📊 Generate Report"):
            st.info("📄 Translation report generated!")
    
    with col3:
        if st.button("🔄 Start New Translation"):
            # Reset all state
            st.session_state.step = "upload"
            st.session_state.uploaded_file = None
            st.session_state.config = None
            st.session_state.result = None
            st.session_state.chat_history = []
            st.rerun()


def main():
    """Main application entry point"""
    render_header()
    
    # Route to appropriate step
    if st.session_state.step == "upload":
        step1_upload()
    elif st.session_state.step == "configure":
        step2_configuration()
    elif st.session_state.step == "workspace":
        step3_workspace()


if __name__ == "__main__":
    main()
