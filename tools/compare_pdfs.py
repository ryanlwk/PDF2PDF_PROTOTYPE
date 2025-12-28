#!/usr/bin/env python3
"""
PDF Comparison Tool
Extracts and compares text from final_output1.pdf and final_output2.pdf
to identify translation differences and issues.
"""

import fitz  # PyMuPDF
import json
import sys
from typing import List, Dict, Tuple
from difflib import SequenceMatcher

def extract_text_from_pdf(pdf_path: str) -> Dict[int, List[Dict]]:
    """
    Extract text blocks from PDF with their positions.
    
    Returns:
        Dict mapping page_index -> List of text blocks with bbox and content
    """
    doc = fitz.open(pdf_path)
    pages_data = {}
    
    for page_idx in range(len(doc)):
        page = doc[page_idx]
        blocks = page.get_text("dict")["blocks"]
        
        text_blocks = []
        for block in blocks:
            if "lines" in block:  # Text block
                text_content = ""
                for line in block["lines"]:
                    for span in line["spans"]:
                        text_content += span["text"]
                
                if text_content.strip():
                    bbox = block["bbox"]
                    text_blocks.append({
                        "bbox": bbox,
                        "content": text_content.strip(),
                        "y0": bbox[1],  # Top edge for sorting
                    })
        
        # Sort by vertical position (top to bottom)
        text_blocks.sort(key=lambda x: (x["y0"], x["bbox"][0]))
        pages_data[page_idx] = text_blocks
    
    doc.close()
    return pages_data

def compare_texts(text1: str, text2: str) -> Tuple[float, List[str]]:
    """
    Compare two texts and return similarity score and differences.
    
    Returns:
        (similarity_ratio, list_of_differences)
    """
    similarity = SequenceMatcher(None, text1, text2).ratio()
    
    differences = []
    if text1 != text2:
        # Simple word-by-word comparison
        words1 = text1.split()
        words2 = text2.split()
        
        # Find differences
        matcher = SequenceMatcher(None, words1, words2)
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag != 'equal':
                if tag == 'replace':
                    differences.append(f"REPLACE: '{' '.join(words1[i1:i2])}' → '{' '.join(words2[j1:j2])}'")
                elif tag == 'delete':
                    differences.append(f"DELETE: '{' '.join(words1[i1:i2])}'")
                elif tag == 'insert':
                    differences.append(f"INSERT: '{' '.join(words2[j1:j2])}'")
    
    return similarity, differences

def compare_pdfs():
    """Main comparison function."""
    pdf1_path = "final_output1.pdf"
    pdf2_path = "final_output2.pdf"
    
    print("=" * 80)
    print("📊 PDF Comparison Tool")
    print("=" * 80)
    print(f"📄 PDF 1 (Preferred): {pdf1_path}")
    print(f"📄 PDF 2 (To Fix):    {pdf2_path}")
    print("=" * 80)
    print()
    
    # Extract text from both PDFs
    print("🔍 Extracting text from PDFs...")
    pdf1_data = extract_text_from_pdf(pdf1_path)
    pdf2_data = extract_text_from_pdf(pdf2_path)
    
    print(f"   PDF 1: {len(pdf1_data)} pages")
    print(f"   PDF 2: {len(pdf2_data)} pages")
    print()
    
    # Compare page by page
    all_issues = []
    
    for page_idx in sorted(set(list(pdf1_data.keys()) + list(pdf2_data.keys()))):
        print("=" * 80)
        print(f"📄 PAGE {page_idx + 1}")
        print("=" * 80)
        
        blocks1 = pdf1_data.get(page_idx, [])
        blocks2 = pdf2_data.get(page_idx, [])
        
        print(f"   PDF 1 blocks: {len(blocks1)}")
        print(f"   PDF 2 blocks: {len(blocks2)}")
        print()
        
        # Try to match blocks by position
        matched_pairs = []
        unmatched_1 = []
        unmatched_2 = []
        
        # Simple matching: find blocks with similar Y positions
        used_indices_2 = set()
        for i, block1 in enumerate(blocks1):
            best_match = None
            best_distance = float('inf')
            best_idx = None
            
            for j, block2 in enumerate(blocks2):
                if j in used_indices_2:
                    continue
                
                # Calculate vertical distance
                y1 = block1["y0"]
                y2 = block2["y0"]
                distance = abs(y1 - y2)
                
                if distance < 20 and distance < best_distance:  # Within 20pt
                    best_match = block2
                    best_distance = distance
                    best_idx = j
            
            if best_match:
                matched_pairs.append((block1, best_match))
                used_indices_2.add(best_idx)
            else:
                unmatched_1.append(block1)
        
        # Find unmatched blocks in PDF 2
        for j, block2 in enumerate(blocks2):
            if j not in used_indices_2:
                unmatched_2.append(block2)
        
        # Compare matched pairs
        print(f"   ✅ Matched pairs: {len(matched_pairs)}")
        print(f"   ⚠️  Unmatched in PDF 1: {len(unmatched_1)}")
        print(f"   ⚠️  Unmatched in PDF 2: {len(unmatched_2)}")
        print()
        
        # Detailed comparison of matched pairs
        page_issues = []
        for idx, (block1, block2) in enumerate(matched_pairs):
            text1 = block1["content"]
            text2 = block2["content"]
            
            similarity, differences = compare_texts(text1, text2)
            
            if similarity < 1.0:  # Different texts
                print(f"   ┌─ Block {idx + 1} ──────────────────────────────────────────────")
                print(f"   │ Position: Y={block1['y0']:.1f}")
                print(f"   │ Similarity: {similarity:.2%}")
                print(f"   │")
                print(f"   │ PDF 1 (Preferred):")
                print(f"   │   {text1[:100]}{'...' if len(text1) > 100 else ''}")
                print(f"   │")
                print(f"   │ PDF 2 (Current):")
                print(f"   │   {text2[:100]}{'...' if len(text2) > 100 else ''}")
                print(f"   │")
                
                if differences:
                    print(f"   │ Differences:")
                    for diff in differences[:3]:  # Show first 3 differences
                        print(f"   │   • {diff}")
                    if len(differences) > 3:
                        print(f"   │   ... ({len(differences) - 3} more)")
                
                print(f"   └───────────────────────────────────────────────────────────────")
                print()
                
                page_issues.append({
                    "block_idx": idx + 1,
                    "position": block1["y0"],
                    "similarity": similarity,
                    "text1": text1,
                    "text2": text2,
                    "differences": differences
                })
        
        # Report unmatched blocks
        if unmatched_1:
            print(f"   ⚠️  Blocks only in PDF 1 (Preferred):")
            for block in unmatched_1[:3]:  # Show first 3
                print(f"      • Y={block['y0']:.1f}: {block['content'][:60]}...")
            if len(unmatched_1) > 3:
                print(f"      ... ({len(unmatched_1) - 3} more)")
            print()
        
        if unmatched_2:
            print(f"   ⚠️  Blocks only in PDF 2 (Current):")
            for block in unmatched_2[:3]:  # Show first 3
                print(f"      • Y={block['y0']:.1f}: {block['content'][:60]}...")
            if len(unmatched_2) > 3:
                print(f"      ... ({len(unmatched_2) - 3} more)")
            print()
        
        all_issues.append({
            "page": page_idx + 1,
            "issues": page_issues,
            "unmatched_1": len(unmatched_1),
            "unmatched_2": len(unmatched_2)
        })
    
    # Summary
    print()
    print("=" * 80)
    print("📊 SUMMARY")
    print("=" * 80)
    
    total_issues = sum(len(p["issues"]) for p in all_issues)
    total_unmatched_1 = sum(p["unmatched_1"] for p in all_issues)
    total_unmatched_2 = sum(p["unmatched_2"] for p in all_issues)
    
    print(f"Total pages compared: {len(all_issues)}")
    print(f"Total text differences: {total_issues}")
    print(f"Blocks only in PDF 1: {total_unmatched_1}")
    print(f"Blocks only in PDF 2: {total_unmatched_2}")
    print()
    
    # Save detailed report
    report_file = "pdf_comparison_report.json"
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump({
            "pdf1": pdf1_path,
            "pdf2": pdf2_path,
            "pages": all_issues,
            "summary": {
                "total_pages": len(all_issues),
                "total_issues": total_issues,
                "unmatched_1": total_unmatched_1,
                "unmatched_2": total_unmatched_2
            }
        }, f, ensure_ascii=False, indent=2)
    
    print(f"💾 Detailed report saved to: {report_file}")
    print()
    
    return all_issues

if __name__ == "__main__":
    try:
        issues = compare_pdfs()
        print("✅ Comparison complete!")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)




