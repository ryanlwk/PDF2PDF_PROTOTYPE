import fitz  # PyMuPDF
import json
import os
import sys

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def clean_text(text):
    """Remove newlines to enable proper justification"""
    if not text: return ""
    return text.replace("\n", "").strip()

def render_pdf():
    """
    V5 Final - Shape-Aware Rendering
    
    Key Improvements:
    1. Main Title Detection - 24pt for page-top headings
    2. Label Detection - Center-aligned 9pt for narrow boxes (table cells, chart nodes)
    3. Standard Body - 10.5pt justified for paragraphs
    4. Fixed font sizes - No more unstable height-based scaling
    """
    input_pdf = "somatosensory.pdf"
    input_json = "translated_layer.json"
    output_pdf = "final_output.pdf"
    
    font_map = {
        "sans-reg": "fonts/NotoSansCJKtc-Regular.otf",
        "sans-bold": "fonts/NotoSansCJKtc-Bold.otf",
        "serif": "fonts/NotoSerifCJKtc-Regular.otf"
    }

    # Verify fonts
    for f in font_map.values():
        if not os.path.exists(f):
            print(f"❌ Missing: {f}")
            return

    print("=" * 60)
    print("🚀 Phase 4 V5: Shape-Aware Rendering")
    print("=" * 60)
    print("✨ Smart Features:")
    print("   • Main title detection (24pt)")
    print("   • Label detection (centered 9pt for table/chart)")
    print("   • Fixed font sizes (stable rendering)")
    print("=" * 60)
    print()

    doc = fitz.open(input_pdf)
    
    with open(input_json, "r", encoding="utf-8") as f:
        data = json.load(f)

    for page_idx, page in enumerate(doc):
        page_data = next((p for p in data["pages"] if p["page_index"] == page_idx), None)
        if not page_data: continue
        
        print(f"📄 Rendering Page {page_idx + 1}...")
        page_h = page.rect.height

        # Register Fonts
        page.insert_font(fontname="sans-reg", fontfile=font_map["sans-reg"])
        page.insert_font(fontname="sans-bold", fontfile=font_map["sans-bold"])
        page.insert_font(fontname="serif", fontfile=font_map["serif"])

        # PASS 1: Smart Redaction (Preserve Graphics)
        for block in page_data["blocks"]:
            if block["type"] in ["image", "chart"]: continue
            if not block["content"]: continue
            
            x0, y0, x1, y1 = block["bbox"]
            rect = fitz.Rect(x0, page_h - y1, x1, page_h - y0)
            page.add_redact_annot(rect)
        
        page.apply_redactions(images=0, graphics=0)

        # Re-register fonts after redaction
        page.insert_font(fontname="sans-reg", fontfile=font_map["sans-reg"])
        page.insert_font(fontname="sans-bold", fontfile=font_map["sans-bold"])
        page.insert_font(fontname="serif", fontfile=font_map["serif"])

        # PASS 2: Shape-Aware Typesetting
        for block in page_data["blocks"]:
            if block["type"] in ["image", "chart"]: continue
            if not block["content"]: continue

            text = clean_text(block["content"])
            if not text: continue

            x0, y0, x1, y1 = block["bbox"]
            rect = fitz.Rect(x0, page_h - y1, x1, page_h - y0)
            
            # --- SHAPE-AWARE HEURISTICS ---
            b_type = block["type"].lower()
            width = rect.width
            height = rect.height
            
            # Defaults
            font_key = "serif"
            start_size = 10.5
            align = 3  # Justified
            
            # Smart Classification Logic
            if b_type == "heading":
                font_key = "sans-bold"
                align = 0  # Left
                
                # Main Title Detection: Page 1, top area (y0 < 200 in visual coords)
                if page_idx == 0 and rect.y0 < 200:
                    start_size = 24  # Large title
                else:
                    start_size = 16  # Section headings
            
            elif b_type == "caption":
                font_key = "sans-reg"
                start_size = 9
                align = 3  # Justified captions
            
            elif b_type == "body":
                # Label Detection: Narrow boxes are likely table cells or chart nodes
                # Criteria: width < 130pt OR very short height
                if width < 130 or height < 20:
                    # This is a LABEL (table cell, chart node)
                    font_key = "sans-reg"  # Sans for UI elements
                    start_size = 9
                    align = 1  # CENTER ALIGN for labels!
                else:
                    # Standard paragraph
                    font_key = "serif"
                    start_size = 10.5
                    align = 3  # Justified
            
            elif b_type in ["table", "footer", "header"]:
                font_key = "sans-reg"
                start_size = 9
                align = 0  # Left
            
            # Apply Padding (manually since deflate doesn't exist)
            if rect.width > 10 and rect.height > 10:
                rect = fitz.Rect(
                    rect.x0 + 2,  # Left padding
                    rect.y0 + 1,  # Top padding
                    rect.x1 - 2,  # Right padding
                    rect.y1 - 1   # Bottom padding
                )

            # Fitting Loop with Fixed Starting Sizes
            fontsize = start_size
            while fontsize >= 6:
                rc = page.insert_textbox(
                    rect, 
                    text, 
                    fontsize=fontsize, 
                    fontname=font_key,
                    align=align,
                    lineheight=1.2
                )
                if rc >= 0: 
                    break  # Success
                fontsize -= 0.5
            
            # Fallback: Force at 6pt if nothing fits
            if fontsize < 6:
                page.insert_textbox(
                    rect, 
                    text, 
                    fontsize=6, 
                    fontname=font_key, 
                    align=align,
                    lineheight=1.1
                )

    doc.save(output_pdf)
    
    print()
    print("=" * 60)
    print("✅ Rendering Complete!")
    print(f"💾 Output: {output_pdf}")
    print("=" * 60)
    print()
    print("🎨 Shape-Aware Features Applied:")
    print("   ✅ Main title: 24pt bold (page 1 top)")
    print("   ✅ Labels: 9pt centered (table/chart)")
    print("   ✅ Body: 10.5pt justified (paragraphs)")
    print("   ✅ Fixed sizes (no unstable scaling)")
    print()

if __name__ == "__main__":
    render_pdf()
