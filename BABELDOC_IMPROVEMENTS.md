# PDF2PDF Improvement Roadmap

## Based on BabelDOC Study (Reference.md)

**Created:** 2025-01-01  
**Status:** Planning Phase  
**Source:** Complete analysis of BabelDOC technical documentation

---

## 📋 Table of Contents

1. [Critical Fixes](#critical-fixes)
2. [High Priority Improvements](#high-priority-improvements)
3. [Medium Priority Enhancements](#medium-priority-enhancements)
4. [Low Priority Polish](#low-priority-polish)
5. [Implementation Checklist](#implementation-checklist)
6. [Technical References](#technical-references)

---

## 🔴 CRITICAL FIXES (Do First)

### 1. Fix Pink Box Issue - White Rectangle Approach

**Reference:** Reference.md Section 11.2, lines 1796-1828  
**Current Problem:** Using `page.add_redact_annot()` creates pink/white box artifacts  
**BabelDOC Solution:** Add white rectangles BEFORE rendering text, not using redaction

**Files to Modify:**

- `tools/render_pdf_v2.py`

**Implementation:**

```python
# REPLACE: page.add_redact_annot() and page.apply_redactions()
# WITH: White rectangle background approach

def add_white_background_before_text(page, blocks):
    """
    Add white rectangles BEFORE rendering text
    This fixes Z-order and eliminates pink boxes
    """
    for block in blocks:
        bbox = block["bbox"]

        # Create shape for white background
        shape = page.new_shape()
        shape.draw_rect(fitz.Rect(bbox))
        shape.finish(
            fill=(1, 1, 1),      # Pure white
            color=None,           # No border
            fill_opacity=1.0      # Fully opaque
        )
        shape.commit()  # Render BEFORE text
```

**Expected Impact:**

- ✅ Eliminates pink boxes completely
- ✅ Proper Z-order (background → text)
- ✅ Clean visual output

**Time Estimate:** 30 minutes  
**Priority:** 🔴 CRITICAL

---

### 2. Font Subsetting (99% Size Reduction)

**Reference:** Reference.md Section 11.2, lines 1746-1763  
**Current Problem:** Embedding full font files (15 MB each)  
**BabelDOC Solution:** Only embed used glyphs (50-200 KB per font)

**Files to Modify:**

- `tools/render_pdf_v2.py`

**Implementation:**

```python
# Add at end of render_pdf_style_aware()

def optimize_pdf_file_size(pdf_path):
    """
    BabelDOC's biggest optimization: Font subsetting
    Reduces font size from 15 MB → 50 KB per font!
    """
    print("🔤 Subsetting fonts...")
    pdf = fitz.open(pdf_path)

    # CRITICAL: Only embed used glyphs
    pdf.subset_fonts()  # 99% reduction!

    # Save with all optimizations
    pdf.save(
        pdf_path,
        garbage=4,              # Aggressive cleanup
        deflate=True,           # Compress streams (60-70%)
        clean=True,             # Remove duplicates
        deflate_fonts=True,     # Compress fonts
        deflate_images=True,    # Compress images
        pretty=False            # Smaller output
    )
    pdf.close()

# Call after rendering
if __name__ == "__main__":
    render_pdf_style_aware()
    optimize_pdf_file_size("final_output.pdf")
```

**Expected Impact:**

- ✅ 30-50% smaller output files
- ✅ Faster loading times
- ✅ Same visual quality

**Metrics:**

- Without subsetting: 45 MB (3 full fonts)
- With subsetting: 150-600 KB (only used glyphs)

**Time Estimate:** 15 minutes  
**Priority:** 🔴 CRITICAL

---

## 🟠 HIGH PRIORITY IMPROVEMENTS

### 3. Character-Level Extraction

**Reference:** Reference.md Section 4.1, lines 257-274  
**Current Problem:** Averaging styles across blocks, losing precision  
**BabelDOC Solution:** Store EVERY character with exact position and style

**Files to Modify:**

- `tools/extract_il_v2.py`
- `intermediate_layer_v2.json` (schema update)

**Key Changes:**

1. Store each span separately (no averaging)
2. Preserve per-character bounding boxes
3. Keep exact font/size/color for each span

**Implementation Notes:**

```python
# Use rawdict to get character-level data
page_dict = page.get_text("rawdict", flags=fitz.TEXT_PRESERVE_WHITESPACE)

# Store EACH SPAN separately
for span in line["spans"]:
    span_data = {
        "text": span["text"],
        "bbox": span["bbox"],
        "style": {
            "font": span["font"],
            "size": span["size"],
            "color": f"#{span['color']:06x}",
            "flags": span["flags"],
            "bold": bool(span["flags"] & 2**4),
            "italic": bool(span["flags"] & 2**1)
        }
    }
```

**Expected Impact:**

- ✅ Precise style preservation per span
- ✅ No more style averaging
- ✅ Better font/color accuracy

**Time Estimate:** 2 hours  
**Priority:** 🟠 HIGH

---

### 4. Alignment Detection (Stop Guessing)

**Reference:** Reference.md Section 5.2, lines 376-442  
**Current Problem:** Guessing alignment based on block type  
**BabelDOC Solution:** Detect ACTUAL alignment from geometry

**Files to Modify:**

- `tools/extract_il_v2.py`

**Key Features:**

1. Detect first-line indent by comparing line x-positions
2. Analyze left/right edge consistency
3. Calculate line spacing ratios
4. Determine center/left/right/justified alignment

**Implementation Notes:**

```python
def detect_alignment_from_geometry(block_dict, page_width):
    """Detect ACTUAL alignment from text positions"""

    # Check for first-line indent
    if len(lines) >= 2:
        indent_diff = line_x0s[0] - line_x0s[1]
        if indent_diff > 15:
            first_line_indent = True

    # Analyze edge consistency
    x0_variance = max(line_x0s) - min(line_x0s)
    x2_variance = max(line_x2s) - min(line_x2s)

    # Determine alignment type
    if x0_variance < 5 and x2_variance < 5:
        alignment = "justified"
    elif x0_variance < 5:
        alignment = "left"
    # ... etc
```

**Expected Impact:**

- ✅ Accurate alignment preservation
- ✅ Proper indentation detection
- ✅ Better text reflow

**Time Estimate:** 1 hour  
**Priority:** 🟠 HIGH

---

### 5. Enhanced Intermediate Layer Schema

**Reference:** Reference.md Section 10.1, lines 1448-1502  
**Current Problem:** Simple block structure, missing metadata  
**BabelDOC Solution:** Comprehensive IL with rendering hints

**Files to Modify:**

- `tools/extract_il_v2.py`
- `tools/translate_il_v2.py`
- `tools/render_pdf_v2.py`

**New Schema Structure:**

```json
{
  "document": {
    "total_pages": 10,
    "source_language": "en",
    "target_language": "zh-Hant",
    "metadata": {
      "creation_date": "2025-01-01T12:00:00Z",
      "tool_version": "v2.1",
      "pipeline_stages_completed": []
    }
  },
  "pages": [
    {
      "page_number": 0,
      "mediabox": [0, 0, 612, 792],
      "blocks": [
        {
          "block_id": 0,
          "reading_order": 0,
          "type": "body",
          "bbox": [72, 650, 540, 720],
          "content": {
            "original": "Original text",
            "translated": "翻译文本"
          },
          "spans": [
            {
              "text": "Original",
              "translated": "翻译",
              "bbox": [72, 700, 95, 712],
              "style": {
                "font": "Times-Roman",
                "size": 12.0,
                "color": "#000000",
                "bold": false,
                "italic": false
              }
            }
          ],
          "layout": {
            "alignment": "justified",
            "first_line_indent": true,
            "line_spacing": 1.2
          },
          "rendering": {
            "render_order": 10,
            "z_order": "text"
          }
        }
      ],
      "images": [
        {
          "xref": 42,
          "bbox": [100, 400, 500, 600],
          "transform_matrix": [1, 0, 0, 1, 0, 0],
          "render_order": 5
        }
      ],
      "graphics": []
    }
  ]
}
```

**Expected Impact:**

- ✅ Complete metadata preservation
- ✅ Better debugging capability
- ✅ Enables advanced features

**Time Estimate:** 3 hours  
**Priority:** 🟠 HIGH

---

### 6. Scanned PDF Detection

**Reference:** Reference.md Section 8.2, lines 816-856  
**Current Problem:** No detection of scanned PDFs  
**BabelDOC Solution:** SSIM-based automatic detection

**Files to Modify:**

- `tools/extract_il_v2.py`

**Implementation Notes:**

```python
# Requires: pip install scikit-image

def detect_if_scanned(pdf_path):
    """
    BabelDOC's SSIM-based scanned PDF detection
    1. Render original page
    2. Remove text and re-render
    3. Compare using SSIM
    4. If similarity > 0.95 → scanned
    """
    from skimage.metrics import structural_similarity as ssim

    # Check first 3 pages
    # If >80% are scanned → enable OCR workaround
```

**Expected Impact:**

- ✅ Automatic scanned PDF detection
- ✅ Better handling of image-based PDFs
- ✅ Prevents invisible text issues

**Time Estimate:** 2 hours  
**Priority:** 🟠 HIGH

---

## 🟡 MEDIUM PRIORITY ENHANCEMENTS

### 7. Image & Chart Preservation

**Reference:** Reference.md Section 7, lines 566-803  
**Current Status:** Basic preservation, no metadata  
**BabelDOC Solution:** Extract with exact positioning and transforms

**Files to Modify:**

- `tools/extract_il_v2.py`
- `intermediate_layer_v2.json`

**Key Features:**

1. Extract raster images with xref
2. Extract vector graphics (drawings)
3. Store transformation matrices
4. Document bounding boxes

**Implementation Notes:**

```python
def extract_images_with_metadata(page):
    images = []

    # Method 1: Raster images
    for img_info in page.get_images(full=True):
        xref = img_info[0]
        img_dict = page.parent.extract_image(xref)
        # Store xref, bbox, dimensions

    # Method 2: Vector graphics
    drawings = page.get_drawings()
    # Store drawing items and rects

    return images
```

**Expected Impact:**

- ✅ Perfect image preservation
- ✅ No image degradation
- ✅ Exact positioning maintained

**Time Estimate:** 2 hours  
**Priority:** 🟡 MEDIUM

---

### 8. Table Detection & Translation

**Reference:** Reference.md Section 9, lines 1050-1443  
**Current Status:** Tables not handled specially  
**BabelDOC Solution:** OCR-based text extraction from tables

**Files to Modify:**

- `tools/extract_il_v2.py` (detection)
- `tools/translate_il_v2.py` (cell-by-cell translation)

**Requirements:**

- `pip install rapidocr-onnxruntime`

**Key Features:**

1. Detect table regions (heuristic: uniform line spacing)
2. Extract cell text via OCR
3. Translate each cell independently
4. Preserve table borders

**Expected Impact:**

- ✅ Table text translation
- ⚠️ Table structure NOT preserved (limitation)
- ✅ Cell positions maintained

**Time Estimate:** 4 hours  
**Priority:** 🟡 MEDIUM

---

### 9. Formula Detection & Preservation

**Reference:** Reference.md Section 6, lines 444-563  
**Current Status:** Formulas translated (breaks them)  
**BabelDOC Solution:** Placeholder system to preserve formulas

**Files to Modify:**

- `tools/translate_il_v2.py`

**Key Features:**

1. Detect LaTeX formulas: `$E=mc^2$`
2. Detect math symbols: `∫∑∏πθα-ω`
3. Replace with placeholders: `{v1}`, `{v2}`
4. Translate text only
5. Restore formulas after translation

**Implementation Notes:**

```python
def detect_formulas_and_create_placeholders(text):
    patterns = [
        r'\$[^\$]+\$',           # LaTeX inline
        r'[a-zA-Z]\s*=\s*[^,\.]+',  # Equations
        r'[∫∑∏πθα-ωΔ∇]+',       # Math symbols
    ]

    # Replace with {v1}, {v2}, etc.
    # Translate
    # Restore formulas
```

**Expected Impact:**

- ✅ Mathematical formulas preserved
- ✅ No broken equations
- ✅ Better scientific paper support

**Time Estimate:** 2 hours  
**Priority:** 🟡 MEDIUM

---

## 🟢 LOW PRIORITY (Polish & UX)

### 10. Progress Monitoring UI

**Reference:** Reference.md Section 3.1, lines 100-238  
**Current Status:** Simple spinner  
**BabelDOC Solution:** 11-stage pipeline visualization

**Files to Modify:**

- `app.py` (step3_workspace function)
- `backend_wrapper.py` (add callbacks)

**Key Features:**

1. Show 7-11 pipeline stages
2. Real-time progress bar
3. Stage-by-stage completion indicators
4. Estimated time remaining

**UI Layout:**

```
🚀 Translation Pipeline
[=========>          ] 45%

Stage 5/11: Translation
🌍 Translating content...

📄 ✅  |  🔍 ✅  |  🎨 ✅  |  🔢 ✅  |  🌍 🔄  |  📏 ⏸️  |  🖨️ ⏸️
```

**Expected Impact:**

- ✅ Better UX
- ✅ User confidence
- ✅ Clear progress indication

**Time Estimate:** 1 hour  
**Priority:** 🟢 LOW

---

### 11. Debug Panel & IL Viewer

**Reference:** Reference.md Section 10.5, lines 1640-1678  
**Current Status:** No debug information visible  
**BabelDOC Solution:** Show IL statistics and block details

**Files to Modify:**

- `app.py` (add debug tab)

**Key Features:**

1. Show IL file contents
2. Display block statistics
3. Block-by-block inspector
4. Style metadata viewer

**UI Layout:**

```
Debug Info Tab
├── Statistics
│   ├── Total Blocks: 45
│   ├── Total Characters: 12,345
│   └── Translated: 45/45
├── Block Inspector
│   ├── Block 1: heading
│   │   ├── bbox: [72, 650, 540, 720]
│   │   └── style: {size: 18, bold: true}
│   └── Block 2: body
```

**Expected Impact:**

- ✅ Better debugging
- ✅ Transparency
- ✅ Development efficiency

**Time Estimate:** 1 hour  
**Priority:** 🟢 LOW

---

### 12. Dual PDF Comparison Mode

**Reference:** Reference.md Section 2.2, lines 85-92  
**Current Status:** Two separate viewers  
**BabelDOC Feature:** Side-by-side with sync scrolling

**Files to Modify:**

- `app.py` (enhance display_pdf function)

**Key Features:**

1. Side-by-side layout
2. Synchronized scrolling
3. Toggle sync on/off
4. Aligned page viewing

**Implementation Notes:**

```javascript
// JavaScript for scroll sync
const left = document.getElementById("pdf_left");
const right = document.getElementById("pdf_right");

left.addEventListener("scroll", () => {
  right.scrollTop = left.scrollTop;
});
```

**Expected Impact:**

- ✅ Better comparison workflow
- ✅ Easier review process
- ✅ Professional appearance

**Time Estimate:** 1 hour  
**Priority:** 🟢 LOW

---

### 13. Block-Level Editor

**Reference:** Reference.md Section 10.1 (IL structure enables editing)  
**Current Status:** No manual editing capability  
**New Feature:** Edit individual blocks before re-rendering

**Files to Modify:**

- `app.py` (add editor tab)

**Key Features:**

1. Select block from list
2. Edit translation manually
3. Adjust style (size, alignment)
4. Re-render with changes

**UI Layout:**

```
Block Editor
├── Select Block: [Block 5: body - "This is..."]
├── Original: "This is the original text."
├── Translation: [editable] "這是原始文本。"
├── Style:
│   ├── Font Size: [slider 6-72]
│   └── Alignment: [left|center|right|justified]
└── [💾 Save and Re-render]
```

**Expected Impact:**

- ✅ Manual refinement capability
- ✅ Quality control
- ✅ User empowerment

**Time Estimate:** 2 hours  
**Priority:** 🟢 LOW

---

## 📊 Implementation Checklist

### Phase 1: Critical Fixes (Week 1)

- [ ] **Day 1-2:** Pink box fix (#1) - White rectangle approach
- [ ] **Day 2:** Font subsetting (#2) - Add optimization function
- [ ] **Day 3-5:** Character-level extraction (#3) - Rewrite extraction logic

### Phase 2: High Priority (Week 2)

- [ ] **Day 1-2:** Alignment detection (#4) - Add geometry analysis
- [ ] **Day 3-4:** Enhanced IL schema (#5) - Update data structures
- [ ] **Day 5:** Scanned PDF detection (#6) - Add SSIM comparison

### Phase 3: Medium Priority (Week 3)

- [ ] **Day 1-2:** Image preservation (#7) - Extract metadata
- [ ] **Day 3-4:** Formula preservation (#9) - Add placeholder system
- [ ] **Day 5:** Optional: Table detection (#8) - If needed

### Phase 4: Polish (Week 4)

- [ ] **Day 1:** Progress monitoring UI (#10) - Add stage indicators
- [ ] **Day 2:** Debug panel (#11) - Add IL viewer
- [ ] **Day 3:** Dual PDF view (#12) - Add sync scrolling
- [ ] **Day 4:** Block editor (#13) - Add manual editing

---

## 🎯 Quick Wins (Can Do Today)

### 1. Font Subsetting (15 minutes)

Add 3 lines to `render_pdf_v2.py`:

```python
pdf = fitz.open("final_output.pdf")
pdf.subset_fonts()
pdf.save("final_output.pdf", garbage=4, deflate=True)
```

**Result:** 30-50% smaller files immediately!

### 2. White Rectangle Fix (30 minutes)

Replace redaction with white rectangles in `render_pdf_v2.py`
**Result:** No more pink boxes!

### 3. Better Alignment Detection (1 hour)

Add geometry-based alignment detection to `extract_il_v2.py`
**Result:** More accurate text layout!

---

## 📚 Technical References

### Key BabelDOC Sections

| Topic               | Reference.md Section | Lines     | Key Insight                |
| ------------------- | -------------------- | --------- | -------------------------- |
| Full Rebuild        | Section 11.2         | 1796-1828 | Remove original text layer |
| Font Subsetting     | Section 11.2         | 1746-1763 | 99% font size reduction    |
| Character-Level     | Section 4.1          | 257-274   | Exact position per char    |
| Alignment Detection | Section 5.2          | 376-442   | Detect from geometry       |
| Scanned Detection   | Section 8.2          | 816-856   | SSIM comparison            |
| Image Preservation  | Section 7            | 566-803   | XObject references         |
| Formula Handling    | Section 6            | 444-563   | Placeholder system         |
| Table Translation   | Section 9            | 1050-1443 | OCR + cell-by-cell         |

### BabelDOC's 11-Stage Pipeline

1. PDF Parsing (pdfminer fork)
2. Scanned Detection (SSIM)
3. Layout Analysis (DocLayout-YOLO)
4. Table Detection (RapidOCR)
5. Paragraph Finding (geometry-based)
6. Style & Formula Processing
7. Term Extraction (optional)
8. Translation (LLM with placeholders)
9. Typesetting (reflow with overflow handling)
10. Font Mapping (Noto fonts)
11. PDF Rendering (with optimization)

### File Size Optimization Techniques

1. **Font Subsetting** (99% reduction) - `pdf.subset_fonts()`
2. **Garbage Collection** (remove unused) - `garbage=4`
3. **DEFLATE Compression** (60-70%) - `deflate=True`
4. **Remove Original Text** (30-50%) - Full rebuild
5. **Resource Deduplication** - Automatic
6. **XObject Reuse** - Reference, not copy
7. **Clean Flag** - `clean=True`

**Expected Result:**

- Original: 10 MB
- Optimized: 3-5 MB (30-50% smaller)

---

## 🎓 Key Learnings from BabelDOC

1. **Full Rebuild > Overlay**

   - Never overlay translated text on original
   - Always rebuild from scratch
   - Eliminates artifacts and reduces size

2. **Character-Level Precision**

   - Store position/style for every character
   - Don't average styles across blocks
   - Enables perfect style preservation

3. **Geometry-Based Detection**

   - Detect alignment from actual positions
   - Don't guess based on heuristics
   - Analyze line edges and spacing

4. **Font Subsetting is Critical**

   - Biggest optimization (99% reduction)
   - Only embed used glyphs
   - 15 MB → 50 KB per font!

5. **Placeholder System for Formulas**

   - Replace formulas with `{v1}`, `{v2}`
   - Translate only text
   - Restore formulas after translation

6. **SSIM for Scanned Detection**

   - Remove text and compare images
   - If similarity > 0.95 → scanned
   - Enable OCR workaround automatically

7. **Intermediate Layer is Key**
   - Decouples parsing from rendering
   - Enables debugging and editing
   - Single source of truth

---

## 🚀 Getting Started

### Immediate Actions (Today)

1. **Read this document completely** ✅
2. **Implement font subsetting** (15 min)

   - Go to `tools/render_pdf_v2.py`
   - Add optimization function
   - Test with sample PDF

3. **Fix pink boxes** (30 min)
   - Replace redaction approach
   - Test with somatosensory.pdf
   - Verify clean output

### This Week

1. Implement critical fixes (#1-2)
2. Start character-level extraction (#3)
3. Test with real PDFs
4. Document results

### This Month

1. Complete high priority items (#3-6)
2. Start medium priority enhancements (#7-9)
3. Add UI polish (#10-13)
4. Final testing and refinement

---

## 📝 Notes

- **No Git Required:** All changes tracked in this document
- **Incremental Approach:** Implement one feature at a time
- **Test After Each Change:** Verify with somatosensory.pdf
- **Keep Reference.md:** Source of truth for implementation details

---

## ✅ Completion Tracking

**Last Updated:** 2025-01-01  
**Items Completed:** 0/13  
**Current Phase:** Planning  
**Next Action:** Implement font subsetting (#2)

---

_This document serves as the complete roadmap for improving PDF2PDF based on BabelDOC's proven techniques. Update completion status as features are implemented._
