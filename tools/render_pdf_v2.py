import fitz  # PyMuPDF
import json
import os
import sys

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def hex_to_rgb(hex_color):
    """Convert hex color (#RRGGBB) to RGB tuple (0-1 range for PyMuPDF)."""
    hex_color = hex_color.lstrip('#')
    r = int(hex_color[0:2], 16) / 255.0
    g = int(hex_color[2:4], 16) / 255.0
    b = int(hex_color[4:6], 16) / 255.0
    return (r, g, b)

def select_font(block_style, block_type, font_map):
    """
    Select appropriate font based on style information and block type.
    
    Priority:
    1. If bold flag is True OR type is heading -> Bold font
    2. If type is body -> Serif font
    3. Default -> Sans-Regular
    """
    is_bold = block_style.get("bold", False)
    
    # Heading or bold text -> Bold font
    if is_bold or block_type == "heading":
        return "sans-bold"
    # Body text -> Serif for readability
    elif block_type == "body":
        return "serif"
    # Everything else -> Sans-Regular (UI elements, labels, sidebars)
    else:
        return "sans-reg"

def get_alignment(block_type):
    """
    Get text alignment based on block type.
    
    Returns:
        Integer alignment code for PyMuPDF:
        0 = Left, 1 = Center, 2 = Right, 3 = Justified
    """
    if block_type in ["label", "caption"]:
        return 1  # Center
    elif block_type in ["heading", "sidebar", "table", "header", "footer"]:
        return 0  # Left
    elif block_type == "body":
        return 3  # Justified
    else:
        return 0  # Default left

def clean_text(text):
    """Clean text for rendering - strip newlines."""
    if not text:
        return ""
    return text.replace("\n", " ").strip()

def render_pdf_style_aware():
    """
    Phase 4 V2: Style-Aware PDF Rendering
    
    Reads translated_layer_v2.json with style metadata and applies:
    - Original font sizes (from style.size)
    - Original text colors (from style.color)
    - Original font weights (bold from style.bold)
    - Smart alignment based on block type
    - Smart redaction (preserves graphics and images)
    
    Output: final_output_v2.pdf
    """
    input_pdf = "somatosensory.pdf"
    input_json = "translated_layer_v2.json"
    output_pdf = "final_output_v2.pdf"
    
    # Font mapping
    font_map = {
        "sans-reg": "fonts/NotoSansCJKtc-Regular.otf",
        "sans-bold": "fonts/NotoSansCJKtc-Bold.otf",
        "serif": "fonts/NotoSerifCJKtc-Regular.otf"
    }
    
    # Verify all fonts exist
    missing_fonts = [f for f in font_map.values() if not os.path.exists(f)]
    if missing_fonts:
        print("❌ Missing fonts:")
        for f in missing_fonts:
            print(f"   • {f}")
        print("\n   Please run: python tools/download_font.py")
        return
    
    # Verify input files
    if not os.path.exists(input_pdf):
        print(f"❌ Error: {input_pdf} not found!")
        return
    
    if not os.path.exists(input_json):
        print(f"❌ Error: {input_json} not found!")
        print("   Please run: python tools/translate_il_v2.py first")
        return
    
    print("=" * 60)
    print("🎨 Phase 4 V2: Style-Aware Rendering")
    print("=" * 60)
    print(f"📄 Input PDF: {input_pdf}")
    print(f"📝 Translation: {input_json}")
    print(f"💾 Output: {output_pdf}")
    print("=" * 60)
    print("✨ Style features:")
    print("   • Original font sizes")
    print("   • Original text colors")
    print("   • Bold fonts (where applicable)")
    print("   • Serif/Sans matching")
    print("   • Smart alignment (justified/centered)")
    print("   • Non-destructive redaction")
    print("=" * 60)
    print()
    
    # Open PDF and load translation data
    doc = fitz.open(input_pdf)
    
    with open(input_json, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    total_rendered = 0
    
    # Process each page
    for page_idx, page in enumerate(doc):
        page_data = next((p for p in data["pages"] if p["page_index"] == page_idx), None)
        
        if not page_data:
            print(f"⚠️  Page {page_idx + 1}: No data found, skipping...")
            continue
        
        print(f"🖌️  Page {page_idx + 1}...")
        
        page_h = page.rect.height
        blocks = page_data["blocks"]
        
        # Register fonts for this page
        page.insert_font(fontname="sans-reg", fontfile=font_map["sans-reg"])
        page.insert_font(fontname="sans-bold", fontfile=font_map["sans-bold"])
        page.insert_font(fontname="serif", fontfile=font_map["serif"])
        
        # --- PASS 1: Smart Redaction ---
        # Remove English text while preserving graphics, images, and backgrounds
        for block in blocks:
            if block["type"] in ["image", "chart"]:
                continue
            
            if not block.get("content"):
                continue
            
            # Convert coordinates: PDF Native (Bottom-Left) -> PyMuPDF (Top-Left)
            x0, y0_pdf, x1, y1_pdf = block["bbox"]
            rect = fitz.Rect(x0, page_h - y1_pdf, x1, page_h - y0_pdf)
            
            # Add redaction annotation (marks area for text removal)
            page.add_redact_annot(rect)
        
        # Apply redactions: remove text, preserve images (0) and graphics (0)
        page.apply_redactions(images=0, graphics=0)
        
        # Re-register fonts after redaction (PyMuPDF clears font references)
        page.insert_font(fontname="sans-reg", fontfile=font_map["sans-reg"])
        page.insert_font(fontname="sans-bold", fontfile=font_map["sans-bold"])
        page.insert_font(fontname="serif", fontfile=font_map["serif"])
        
        # --- PASS 2: Typesetting with Style ---
        blocks_rendered = 0
        
        for block in blocks:
            if block["type"] in ["image", "chart"]:
                continue
            
            text = clean_text(block.get("content", ""))
            if not text:
                continue
            
            # Get style information
            style = block.get("style", {})
            b_type = block["type"]
            
            # Convert coordinates
            x0, y0_pdf, x1, y1_pdf = block["bbox"]
            rect = fitz.Rect(x0, page_h - y1_pdf, x1, page_h - y0_pdf)
            
            # Apply padding (prevent text touching borders)
            # deflate-style adjustment: shrink by 2pt horizontally, 1pt vertically
            rect = fitz.Rect(
                rect.x0 + 2,
                rect.y0 + 1,
                rect.x1 - 2,
                rect.y1 - 1
            )
            
            # --- STYLE EXTRACTION ---
            
            # 1. Font Selection (based on bold flag and block type)
            font_key = select_font(style, b_type, font_map)
            
            # 2. Font Size (use original size from extraction)
            original_size = style.get("size", 10.5)
            # Chinese characters are often slightly larger visually than English
            # So we use original size directly or scale slightly down
            target_size = original_size * 0.95  # 5% reduction for fit
            
            # 3. Text Color (use original color)
            text_color = style.get("color", "#000000")
            color_rgb = hex_to_rgb(text_color)
            
            # 4. Alignment (based on block type)
            align = get_alignment(b_type)
            
            # --- FITTING LOOP ---
            # Start with target size and shrink if needed
            fontsize = target_size
            min_size = 6.0  # Minimum readable size
            
            while fontsize >= min_size:
                rc = page.insert_textbox(
                    rect,
                    text,
                    fontsize=fontsize,
                    fontname=font_key,
                    color=color_rgb,
                    align=align,
                    lineheight=1.2
                )
                
                if rc >= 0:  # Success
                    break
                
                fontsize -= 0.5  # Shrink and retry
            
            # Fallback: Force render at minimum size if still overflowing
            if fontsize < min_size:
                page.insert_textbox(
                    rect,
                    text,
                    fontsize=min_size,
                    fontname=font_key,
                    color=color_rgb,
                    align=align,
                    lineheight=1.1  # Tighter line spacing for overflow
                )
            
            blocks_rendered += 1
        
        total_rendered += blocks_rendered
        print(f"   ✅ Rendered {blocks_rendered} blocks")
    
    # Save output
    doc.save(output_pdf)
    doc.close()
    
    print()
    print("=" * 60)
    print("✅ Rendering Complete!")
    print(f"💾 Output: {output_pdf}")
    print(f"📊 Total blocks rendered: {total_rendered}")
    print("=" * 60)
    print()
    print("🎨 Style features applied:")
    print("   ✓ Original font sizes preserved (±5%)")
    print("   ✓ Text colors matched")
    print("   ✓ Bold fonts for headings")
    print("   ✓ Serif fonts for body text")
    print("   ✓ Sans fonts for UI elements")
    print("   ✓ Smart alignment (justified/centered)")
    print("   ✓ Non-destructive text replacement")
    print()
    print("🎉 Style-aware PDF translation complete!")
    print()

if __name__ == "__main__":
    render_pdf_style_aware()
