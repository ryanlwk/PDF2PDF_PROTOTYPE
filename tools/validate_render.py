#!/usr/bin/env python3
"""
Validation tool to check extraction vs rendering completeness.
Ensures all blocks from intermediate_layer_v2.json were rendered.
"""
import json
import sys

def validate_rendering():
    il_file = "intermediate_layer_v2.json"
    log_file = "rendering_log.json"
    
    try:
        with open(il_file) as f:
            il_data = json.load(f)
    except FileNotFoundError:
        print(f"❌ {il_file} not found")
        return False
    
    try:
        with open(log_file) as f:
            log_data = json.load(f)
    except FileNotFoundError:
        print(f"❌ {log_file} not found - run render_pdf_v2.py first")
        return False
    
    # Count extracted blocks
    total_extracted = 0
    extracted_ids = set()
    
    for page in il_data["pages"]:
        for block in page["blocks"]:
            # Skip image/chart blocks (not rendered as text)
            if block["type"] not in ["image", "chart"]:
                total_extracted += 1
                extracted_ids.add(block["id"])
    
    # Count rendered blocks
    rendered_ids = {b["id"] for b in log_data["rendered_blocks"]}
    failed_ids = {b["id"] for b in log_data.get("failed_blocks", [])}
    
    # Calculate coverage
    missing_ids = extracted_ids - rendered_ids - failed_ids
    success_rate = (len(rendered_ids) / total_extracted * 100) if total_extracted > 0 else 0
    
    # Report
    print("=" * 60)
    print("📊 Rendering Validation Report")
    print("=" * 60)
    print(f"Total text blocks extracted:  {total_extracted}")
    print(f"Successfully rendered:        {len(rendered_ids)} ({success_rate:.1f}%)")
    print(f"Failed to fit (forced):       {len(failed_ids)}")
    print(f"Missing (not attempted):      {len(missing_ids)}")
    print("=" * 60)
    
    if missing_ids:
        print("\n⚠️  Missing blocks (never attempted):")
        for page in il_data["pages"]:
            page_missing = [b for b in page["blocks"] if b["id"] in missing_ids]
            if page_missing:
                print(f"\n   Page {page['page_index'] + 1}:")
                for b in page_missing[:3]:
                    print(f"      • {b['type']}: {b['content'][:40]}...")
    
    if success_rate >= 95:
        print("\n✅ PASS: Rendering coverage >= 95%")
        return True
    else:
        print("\n❌ FAIL: Rendering coverage < 95%")
        return False

if __name__ == "__main__":
    success = validate_rendering()
    sys.exit(0 if success else 1)



