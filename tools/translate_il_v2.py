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
MODEL_NAME = os.getenv("OPENROUTER_MODEL", "google/gemini-2.5-flash-preview-09-2025")

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
    
    # System prompt - Updated to match translate_il.py style (full translation)
    system_prompt = (
        "You are a professional academic translator. "
        "Translate the 'content' field of the provided JSON blocks into Traditional Chinese (Hong Kong). "
        "Translate ALL text including technical terms into Chinese. "
        "Only keep well-known proper nouns (person names, place names) in original form if they are internationally recognized. "
        "Translate technical terms like 'receptors', 'corpuscles', 'nociceptors' etc. into their Chinese equivalents. "
        "Strictly maintain the 'id' and 'type' fields unchanged. "
        "Do not translate 'type' values. "
        "Return ONLY a valid JSON object with a single key 'translated_blocks' containing the translated list. "
        "Ensure the output is valid JSON."
    )
    
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
            
            # Parse response - Match translate_il.py format
            response_text = response.choices[0].message.content.strip()
            
            # Handle case where response is wrapped in json markdown
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()
            
            result = json.loads(response_text)
            translated_result = result.get("translated_blocks", [])
            
            # Validate that we got translations
            if not translated_result:
                raise ValueError("API returned empty translated_blocks")
            
            if len(translated_result) != len(translatable):
                print(f"\n⚠️  Warning: Page {page_idx + 1} - Expected {len(translatable)} blocks, got {len(translated_result)}")
            
            # Validate at least one block was actually translated (contains Chinese characters)
            has_chinese = any('\u4e00' <= c <= '\u9fff' for block in translated_result for c in str(block.get('content', '')))
            if not has_chinese:
                raise ValueError("API did not return Chinese translations")
            
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
    
    Reads intermediate_layer.json and translates text content while
    preserving all style metadata (size, color, bold, italic, etc.)
    
    Output: translated_layer.json
    """
    input_file = "intermediate_layer.json"
    output_file = "translated_layer.json"
    
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
        print("👉 Next step: python tools/render_pdf.py")
    print()

if __name__ == "__main__":
    translate_il_v2()








