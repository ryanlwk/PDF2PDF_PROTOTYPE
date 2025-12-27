import json
import os
import sys
import time
from openai import OpenAI
from dotenv import load_dotenv
from tqdm import tqdm

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Load environment variables
load_dotenv()

# Configuration
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
MODEL_NAME = os.getenv("OPENROUTER_MODEL", "google/gemini-2.0-flash-exp:free")

# Initialize OpenRouter client
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY
)

def translate_page_blocks(blocks, page_idx, max_retries=5):
    """
    Translate all translatable blocks on a page using LLM.
    
    Args:
        blocks: List of block dictionaries with content and style
        page_idx: Current page index (for logging)
        max_retries: Maximum retry attempts for API errors
        
    Returns:
        List of translated blocks with preserved style metadata, or None if failed
    """
    # Filter translatable blocks
    translatable_types = ["body", "heading", "caption", "sidebar", "label", "table", "footer", "header"]
    translatable = [b for b in blocks if b["type"] in translatable_types and b.get("content")]
    
    if not translatable:
        return []
    
    # Prepare simplified payload (only send what's needed for translation)
    payload = [
        {
            "id": b["id"],
            "type": b["type"],
            "content": b["content"]
        }
        for b in translatable
    ]
    
    # System prompt
    system_prompt = """You are a professional translator specializing in academic and technical documents.

Translate the following English text blocks into Traditional Chinese (繁體中文, Taiwan standard).

**Critical Rules:**
1. Preserve technical terminology accuracy
2. Maintain formal academic tone
3. Do NOT translate:
   - Proper nouns (names, places)
   - Technical abbreviations (e.g., "CNS", "PNS")
   - Figure/Table references (keep "Figure 1" as "圖 1")
4. Return ONLY valid JSON in this exact format:
   [{"id": "...", "content": "translated text"}, ...]
5. Preserve the order and IDs exactly as given
6. Do NOT add explanations or comments

Translate naturally and professionally."""
    
    # Retry loop with exponential backoff
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": json.dumps(payload, ensure_ascii=False)}
                ],
                response_format={"type": "json_object"},
                temperature=0.3
            )
            
            # Parse response
            response_text = response.choices[0].message.content.strip()
            
            # Handle case where response is wrapped in json markdown
            if response_text.startswith("```json"):
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif response_text.startswith("```"):
                response_text = response_text.split("```")[1].split("```")[0].strip()
            
            translated_result = json.loads(response_text)
            
            # Validate response structure
            if isinstance(translated_result, dict) and "translations" in translated_result:
                translated_result = translated_result["translations"]
            
            if not isinstance(translated_result, list):
                raise ValueError("Response is not a list")
            
            # Validate Chinese characters exist
            has_chinese = any(
                any('\u4e00' <= c <= '\u9fff' for c in item.get("content", ""))
                for item in translated_result
            )
            
            if not has_chinese:
                print(f"\n⚠️  Page {page_idx + 1}: No Chinese characters detected. Retrying...")
                time.sleep(2 ** attempt)
                continue
            
            # Merge translations back with original blocks (preserve style!)
            result_dict = {item["id"]: item["content"] for item in translated_result}
            
            translated_blocks = []
            for block in translatable:
                if block["id"] in result_dict:
                    translated_text = result_dict[block["id"]].strip()
                    # Strip newlines for clean rendering
                    translated_text = translated_text.replace("\n", " ")
                    
                    translated_blocks.append({
                        "id": block["id"],
                        "type": block["type"],
                        "bbox": block["bbox"],
                        "content": translated_text,  # Translated content
                        "style": block["style"],  # Preserve original style!
                        "metadata": block.get("metadata", {})
                    })
            
            return translated_blocks
            
        except Exception as e:
            error_msg = str(e)
            
            # Check for rate limit
            if "429" in error_msg or "rate" in error_msg.lower():
                wait_time = 2 ** attempt
                print(f"\n⚠️  Page {page_idx + 1} - Rate limited. Waiting {wait_time}s... (Attempt {attempt + 1}/{max_retries})")
                time.sleep(wait_time)
                continue
            
            # Other errors
            print(f"\n⚠️  Page {page_idx + 1} - Error: {error_msg}. Retrying... (Attempt {attempt + 1}/{max_retries})")
            time.sleep(2 ** attempt)
    
    # Failed after all retries
    print(f"\n❌ Page {page_idx + 1}: Failed after {max_retries} retries")
    return None

def translate_il_v2():
    """
    Phase 3 V2: Translate Style-Aware Intermediate Layer
    
    Reads intermediate_layer_v2.json and translates text content while
    preserving all style metadata (size, color, bold, italic, etc.)
    
    Output: translated_layer_v2.json
    """
    input_file = "intermediate_layer_v2.json"
    output_file = "translated_layer_v2.json"
    
    if not os.path.exists(input_file):
        print(f"❌ Error: {input_file} not found!")
        print("   Please run: python tools/extract_il_v2.py first")
        return
    
    print("🔧 Configuration:")
    print(f"   Model: {MODEL_NAME}")
    print(f"   API Key: {OPENROUTER_API_KEY[:10]}...{OPENROUTER_API_KEY[-6:]}")
    print()
    
    print("=" * 60)
    print("🚀 Phase 3 V2: Style-Aware Translation")
    print("=" * 60)
    print(f"📋 Model: {MODEL_NAME}")
    print(f"📄 Input: {input_file}")
    print(f"💾 Output: {output_file}")
    print("=" * 60)
    print()
    
    # Load input data
    with open(input_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    output_data = {
        "filename": data["filename"],
        "total_pages": data["total_pages"],
        "version": "2.0",
        "description": "Translated with preserved style metadata",
        "pages": []
    }
    
    total_blocks = 0
    translated_blocks = 0
    failed_pages = []
    
    # Process each page
    for page_data in tqdm(data["pages"], desc="Translating Pages"):
        page_idx = page_data["page_index"]
        blocks = page_data["blocks"]
        
        # Translate page blocks
        result = translate_page_blocks(blocks, page_idx)
        
        if result is None:
            # Translation failed, keep original
            failed_pages.append(page_idx + 1)
            output_data["pages"].append(page_data)
            total_blocks += len(blocks)
        else:
            # Translation succeeded
            output_data["pages"].append({
                "page_index": page_idx,
                "width": page_data["width"],
                "height": page_data["height"],
                "blocks": result
            })
            total_blocks += len(blocks)
            translated_blocks += len(result)
            print(f"   ✅ Page {page_idx + 1}: Translated {len(result)} blocks")
    
    # Save output
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    
    print()
    print("=" * 60)
    print("📊 Translation Summary:")
    print(f"   ✅ Total blocks processed: {total_blocks}")
    print(f"   ✅ Blocks translated: {translated_blocks}")
    print(f"   📄 Pages processed: {data['total_pages']}")
    
    if failed_pages:
        print(f"   ⚠️  Failed pages: {failed_pages}")
        print(f"   ⚠️  Status: PARTIALLY completed")
    else:
        print(f"   ✅ Status: ALL pages completed")
    
    print(f"   💾 Output: {output_file}")
    print("=" * 60)
    print()
    
    if failed_pages:
        print("⚠️  Some pages failed. You can re-run this script to retry.")
    else:
        print("✅ Translation complete!")
        print("👉 Next step: python tools/render_pdf_v2.py")
    print()

if __name__ == "__main__":
    translate_il_v2()

