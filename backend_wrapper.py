"""
Backend wrapper for PDF translation pipeline.
Runs existing tools via subprocess without modifying them.
"""
import os
import sys
import subprocess
import tempfile
import shutil
from pathlib import Path
from typing import Optional


def run_pipeline_subprocess(uploaded_file, api_key: str, model_name: str = None) -> str:
    """
    Run the complete PDF translation pipeline using subprocess.
    
    Args:
        uploaded_file: Streamlit uploaded file object or file path string
        api_key: OpenRouter API key
        model_name: OpenRouter model name (optional, defaults to environment variable)
        
    Returns:
        Path to the generated output PDF file (standardized to 'translated_output.pdf')
        
    Raises:
        Exception: If any step fails or output file is not found
    """
    # Step 1: Sandbox Setup
    temp_dir = tempfile.mkdtemp(prefix="pdf2pdf_")
    
    try:
        # Copy fonts directory to temp_dir
        fonts_src = os.path.join(os.getcwd(), "fonts")
        fonts_dst = os.path.join(temp_dir, "fonts")
        if os.path.exists(fonts_src):
            shutil.copytree(fonts_src, fonts_dst)
        else:
            raise Exception(f"Fonts directory not found: {fonts_src}")
        
        # Save uploaded file as somatosensory.pdf (masquerade)
        if hasattr(uploaded_file, 'read'):
            # Streamlit uploaded file
            input_path = os.path.join(temp_dir, "somatosensory.pdf")
            with open(input_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
        else:
            # File path string
            src_path = uploaded_file
            if not os.path.isabs(src_path):
                src_path = os.path.abspath(src_path)
            input_path = os.path.join(temp_dir, "somatosensory.pdf")
            shutil.copy(src_path, input_path)
        
        # Step 2: Environment Setup
        env = os.environ.copy()
        env["PYTHONPATH"] = os.getcwd()
        env["OPENROUTER_API_KEY"] = api_key
        env["OPENAI_API_KEY"] = api_key  # Some tools may check this
        if model_name:
            env["OPENROUTER_MODEL"] = model_name
        
        # Get Python executable
        python_exe = sys.executable
        
        # Get tools directory
        tools_dir = os.path.join(os.getcwd(), "tools")
        
        # Step 3: Execute Pipeline
        
        # 3.1: Extract
        extract_script = os.path.join(tools_dir, "extract_il_v2.py")
        extract_cmd = [python_exe, extract_script, input_path]
        
        result = subprocess.run(
            extract_cmd,
            cwd=temp_dir,
            env=env,
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            error_msg = f"Extraction failed:\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
            raise Exception(error_msg)
        
        # 3.2: Translate
        translate_script = os.path.join(tools_dir, "translate_il_v2.py")
        translate_cmd = [python_exe, translate_script]
        
        result = subprocess.run(
            translate_cmd,
            cwd=temp_dir,
            env=env,
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            error_msg = f"Translation failed:\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
            raise Exception(error_msg)
        
        # 3.3: Render
        render_script = os.path.join(tools_dir, "render_pdf_v2.py")
        render_cmd = [python_exe, render_script]
        
        result = subprocess.run(
            render_cmd,
            cwd=temp_dir,
            env=env,
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            error_msg = f"Rendering failed:\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
            raise Exception(error_msg)
        
        # Step 4: Standardization - Find and copy output file to project directory
        possible_names = [
            "final_output.pdf",
            "final_output_consistent.pdf",
            "output_tc.pdf"
        ]

        output_pdf = None
        for name in possible_names:
            candidate_path = os.path.join(temp_dir, name)
            if os.path.exists(candidate_path):
                output_pdf = candidate_path
                break

        if output_pdf is None:
            raise Exception(
                f"Output PDF not found in {temp_dir}. "
                f"Files present: {os.listdir(temp_dir)}"
            )

        # CRITICAL: Copy to project directory with standardized name
        project_output_path = os.path.join(os.getcwd(), "translated_output.pdf")
        shutil.copy(output_pdf, project_output_path)
        
        # Clean up temp directory after successful copy
        try:
            shutil.rmtree(temp_dir, ignore_errors=True)
        except:
            pass

        return project_output_path
        
    except Exception as e:
        # Cleanup on error
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir, ignore_errors=True)
        raise
