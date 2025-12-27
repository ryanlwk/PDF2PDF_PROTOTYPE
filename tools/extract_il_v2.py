import fitz  # PyMuPDF
import json
import os
import sys
from collections import Counter

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def get_dominant_style(block_dict):
    """
    Analyzes spans in a block to find the most common style attributes.
    
    Args:
        block_dict: PyMuPDF block dictionary containing lines and spans
        
    Returns:
        Dictionary with 'content' and 'style' keys, or None if empty
    """
    sizes = []
    colors = []
    fonts = []
    text_parts = []
    
    for line in block_dict.get("lines", []):
        for span in line.get("spans", []):
            text_parts.append(span["text"])
            sizes.append(span["size"])
            colors.append(span["color"])  # Integer sRGB
            fonts.append(span["font"])
    
    if not sizes:
        return None
    
    # Calculate dominant attributes
    avg_size = sum(sizes) / len(sizes)
    common_color_int = Counter(colors).most_common(1)[0][0]
    
    # Convert color to hex
    r = (common_color_int >> 16) & 0xFF
    g = (common_color_int >> 8) & 0xFF
    b = common_color_int & 0xFF
    hex_color = f"#{r:02x}{g:02x}{b:02x}"
    
    # Determine Font Flags
    font_name = Counter(fonts).most_common(1)[0][0].lower()
    is_bold = "bold" in font_name or "black" in font_name
    is_italic = "italic" in font_name or "oblique" in font_name
    is_serif = "serif" in font_name or "times" in font_name
    
    content = " ".join(text_parts).strip()
    
    return {
        "content": content,
        "style": {
            "size": round(avg_size, 1),
            "color": hex_color,
            "bold": is_bold,
            "italic": is_italic,
            "serif": is_serif,
            "font_name": font_name
        }
    }

def classify_block(style_data, bbox, page_idx):
    """
    Apply heuristic classification based on geometric and style properties.
    
    Args:
        style_data: Dictionary with 'content' and 'style'
        bbox: Bounding box [x0, y0_fitz, x1, y1_fitz] in PyMuPDF coords
        page_idx: Current page index
        
    Returns:
        Block type string (heading, body, sidebar, label, caption)
    """
    x0, y0_fitz, x1, y1_fitz = bbox
    width = x1 - x0
    height = y1_fitz - y0_fitz
    
    s = style_data["style"]
    content_lower = style_data["content"].lower()
    
    # Default type
    b_type = "body"
    
    # 1. Heading Detection: Large size OR bold+medium size
    if s["size"] > 14 or (s["size"] > 11 and s["bold"]):
        b_type = "heading"
    
    # 2. Sidebar/Remark Detection (Pink box area, margin notes)
    # Right side (x > 350) OR left margin (x < 100), AND narrow width (< 250)
    elif width < 250 and (x0 > 350 or x0 < 100):
        b_type = "sidebar"
    
    # 3. Caption Detection: Starts with figure/table keywords
    elif any(content_lower.startswith(prefix) for prefix in 
            ["figure", "table", "fig", "tab", "圖", "表"]):
        b_type = "caption"
    
    # 4. Chart Label Detection: Small text in narrow boxes
    elif s["size"] < 10 and width < 150:
        b_type = "label"
    
    # 5. Footer/Header Detection: At page extremes
    # Note: y0_fitz is from top, so small y = header, large y = footer
    elif y0_fitz < 50:
        b_type = "header"
    elif y0_fitz > 650:  # Assuming ~700pt page height
        b_type = "footer"
    
    return b_type

def extract_pdf_style_aware():
    """
    Phase 2 V2: Style-Aware PDF Extraction
    
    Uses PyMuPDF to extract text with full style information:
    - Font size
    - Font color (hex)
    - Bold/Italic flags
    - Font family (serif/sans)
    
    Also applies smart classification heuristics for:
    - Headings (large/bold text)
    - Sidebars (narrow boxes on margins)
    - Captions (starts with "Figure", "Table")
    - Labels (small text in narrow boxes)
    - Headers/Footers (page extremes)
    
    Output: intermediate_layer_v2.json with style metadata
    """
    input_pdf = "somatosensory.pdf"
    output_file = "intermediate_layer_v2.json"
    
    if not os.path.exists(input_pdf):
        print(f"❌ Error: {input_pdf} not found!")
        return
    
    print("=" * 60)
    print("🚀 Phase 2 V2: Style-Aware Extraction (PyMuPDF)")
    print("=" * 60)
    print(f"📄 Input: {input_pdf}")
    print(f"💾 Output: {output_file}")
    print("=" * 60)
    print("✨ Extracting:")
    print("   • Font sizes (exact pt values)")
    print("   • Text colors (hex format)")
    print("   • Bold/Italic flags")
    print("   • Serif vs Sans classification")
    print("   • Smart block type detection")
    print("=" * 60)
    print()
    
    doc = fitz.open(input_pdf)
    
    output_data = {
        "filename": input_pdf,
        "total_pages": len(doc),
        "version": "2.0",
        "description": "Style-aware extraction with font metadata",
        "pages": []
    }
    
    total_blocks = 0
    all_types = Counter()
    
    for p_idx, page in enumerate(doc):
        page_h = page.rect.height
        page_w = page.rect.width
        blocks_raw = page.get_text("dict")["blocks"]
        
        parsed_blocks = []
        
        for b in blocks_raw:
            # Skip image blocks (type 1), only process text blocks (type 0)
            if b["type"] != 0:
                continue
            
            style_data = get_dominant_style(b)
            if not style_data or not style_data["content"]:
                continue
            
            # Get bounding box in PyMuPDF coordinates (Top-Left origin)
            x0, y0_fitz, x1, y1_fitz = b["bbox"]
            
            # Classify block based on geometry and style
            b_type = classify_block(style_data, b["bbox"], p_idx)
            
            # Convert to PDF Native Coordinates (Bottom-Left origin)
            # PDF y0 (bottom edge) = page_height - fitz y1 (bottom in visual coords)
            # PDF y1 (top edge) = page_height - fitz y0 (top in visual coords)
            pdf_bbox = [x0, page_h - y1_fitz, x1, page_h - y0_fitz]
            
            # Generate unique ID
            block_id = f"p{p_idx}_x{int(x0)}_y{int(page_h - y0_fitz)}"
            
            # Calculate geometric properties
            width = x1 - x0
            height = y1_fitz - y0_fitz
            
            block_entry = {
                "id": block_id,
                "type": b_type,
                "bbox": pdf_bbox,
                "content": style_data["content"],
                "style": style_data["style"],
                "metadata": {
                    "page": p_idx,
                    "width": round(width, 2),
                    "height": round(height, 2)
                }
            }
            parsed_blocks.append(block_entry)
            all_types[b_type] += 1
            total_blocks += 1
        
        output_data["pages"].append({
            "page_index": p_idx,
            "width": page_w,
            "height": page_h,
            "blocks": parsed_blocks
        })
        
        # Count by type for this page
        page_types = Counter(b["type"] for b in parsed_blocks)
        type_summary = ", ".join(f"{t}:{c}" for t, c in sorted(page_types.items()))
        
        print(f"📄 Page {p_idx + 1}: {len(parsed_blocks)} blocks ({type_summary})")
    
    # Save output
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    
    print()
    print("=" * 60)
    print("✅ Extraction Complete!")
    print(f"💾 Saved: {output_file}")
    print("=" * 60)
    print()
    print("📊 Summary:")
    print(f"   Total blocks: {total_blocks}")
    for btype, count in sorted(all_types.items()):
        print(f"   • {btype}: {count}")
    print()
    print("👉 Next step: python tools/translate_il_v2.py")
    print()

if __name__ == "__main__":
    extract_pdf_style_aware()
