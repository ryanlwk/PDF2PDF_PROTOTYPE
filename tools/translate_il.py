import json
import os
import sys
import time
from typing import List, Dict, Optional
from dotenv import load_dotenv
from openai import OpenAI
from tqdm import tqdm

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Load env
load_dotenv()

API_KEY = os.getenv("OPENROUTER_API_KEY")
MODEL_NAME = os.getenv("OPENROUTER_MODEL", "google/gemini-2.5-flash-preview-09-2025")

if not API_KEY or API_KEY == "sk-or-your-key-here":
    print("⚠️  CRITICAL ERROR: API Key not set.")
    print("👉 Please open '.env' file and paste your OpenRouter API Key.")
    sys.exit(1)

print(f"🔧 Using Model: {MODEL_NAME}")
print(f"🔑 API Key: {API_KEY[:15]}...{API_KEY[-5:]}")

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=API_KEY,
    # OpenRouter specific headers
    default_headers={
        "HTTP-Referer": "https://github.com/PDF2PDF", 
        "X-Title": "PDF2PDF Prototype"
    }
)

def translate_batch(blocks: List[Dict], page_num: int = 0) -> Optional[List[Dict]]:
    """Translates a list of block dicts using LLM with retry logic
    
    Args:
        blocks: List of block dictionaries to translate
        page_num: Page number for better error reporting
        
    Returns:
        List of translated blocks or None if all retries failed
    """
    if not blocks: 
        return []

    # Simplify payload (only send what's needed)
    payload = [{"id": b["id"], "type": b["type"], "content": b["content"]} for b in blocks]

    system_prompt = (
        "You are a professional academic translator. "
        "Translate the 'content' field of the provided JSON blocks into Traditional Chinese (Hong Kong). "
        "Strictly maintain the 'id' and 'type' fields unchanged. "
        "Do not translate 'type' values. "
        "Return ONLY a valid JSON object with a single key 'translated_blocks' containing the translated list. "
        "Ensure the output is valid JSON."
    )

    max_retries = 5
    
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": json.dumps(payload, ensure_ascii=False)}
                ],
                response_format={"type": "json_object"},
                temperature=0.3,  # Lower temperature for more consistent translation
            )
            
            content = response.choices[0].message.content
            
            # Clean up potential markdown code blocks
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
                
            result = json.loads(content)
            translated = result.get("translated_blocks", [])
            
            # Validate that we got translations
            if not translated:
                raise ValueError("API returned empty translated_blocks")
            
            if len(translated) != len(blocks):
                print(f"\n⚠️  Warning: Page {page_num+1} - Expected {len(blocks)} blocks, got {len(translated)}")
            
            # Validate at least one block was actually translated (contains Chinese characters)
            has_chinese = any('\u4e00' <= c <= '\u9fff' for block in translated for c in str(block.get('content', '')))
            if not has_chinese:
                raise ValueError("API did not return Chinese translations")
            
            print(f"\n✅ Page {page_num+1}: Successfully translated {len(translated)} blocks")
            return translated

        except Exception as e:
            wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s, 8s, 16s
            error_msg = str(e)
            
            # Provide more specific error messages
            if "400" in error_msg:
                print(f"\n⚠️  Page {page_num+1} - API Error (400): Model may not support this request. Retrying... (Attempt {attempt + 1}/{max_retries})")
            elif "rate_limit" in error_msg.lower():
                print(f"\n⚠️  Page {page_num+1} - Rate limit hit. Waiting {wait_time}s... (Attempt {attempt + 1}/{max_retries})")
            else:
                print(f"\n⚠️  Page {page_num+1} - Error: {error_msg}. Retrying in {wait_time}s... (Attempt {attempt + 1}/{max_retries})")
            
            if attempt < max_retries - 1:  # Don't sleep on the last failed attempt
                time.sleep(wait_time)
            else:
                print(f"\n❌ Page {page_num+1}: Failed after {max_retries} retries")
                return None
    
    return None

def main(test_mode: bool = False, max_pages: int = None):
    """Main translation function
    
    Args:
        test_mode: If True, only process first page and save to test file
        max_pages: Maximum number of pages to process (None = all)
    """
    input_file = "intermediate_layer.json"
    output_file = "translated_layer_test.json" if test_mode else "translated_layer.json"

    if not os.path.exists(input_file):
        print(f"❌ File not found: {input_file}. Please run Phase 2 first.")
        return False

    print(f"\n{'='*60}")
    print(f"🚀 Starting Translation")
    print(f"📋 Model: {MODEL_NAME}")
    print(f"📄 Input: {input_file}")
    print(f"💾 Output: {output_file}")
    if test_mode:
        print(f"🧪 TEST MODE: Processing first page only")
    if max_pages:
        print(f"📊 Max Pages: {max_pages}")
    print(f"{'='*60}\n")
    
    with open(input_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Limit pages if in test mode or max_pages specified
    pages_to_process = data["pages"]
    if test_mode:
        pages_to_process = pages_to_process[:1]
    elif max_pages:
        pages_to_process = pages_to_process[:max_pages]

    # Track statistics
    total_blocks_processed = 0
    total_blocks_translated = 0
    failed_pages = []

    # Process pages
    for page_idx, page in enumerate(tqdm(pages_to_process, desc="Translating Pages")):
        
        # 1. Identify translatable blocks
        batch_blocks = []
        for block in page["blocks"]:
            # Filter logic: Must be text-based type and not a placeholder
            if block["type"] in ["body", "heading", "caption", "chart", "table", "footer", "header", "sidebar", "label"]:
                if block["content"] and not block["content"].startswith("["):
                    batch_blocks.append(block)
        
        total_blocks_processed += len(batch_blocks)
        
        # 2. Translate
        if batch_blocks:
            translated_result = translate_batch(batch_blocks, page_num=page_idx)
            
            if translated_result is None:
                # Translation failed
                failed_pages.append(page_idx + 1)
                print(f"\n⚠️  Page {page_idx+1}: Skipping translation due to errors")
                continue
            
            # 3. Create a mapping for quick lookup
            trans_map = {item["id"]: item["content"] for item in translated_result}
            
            # 4. Apply translations back to the original blocks
            translated_count = 0
            for block in page["blocks"]:
                if block["id"] in trans_map:
                    block["content"] = trans_map[block["id"]]
                    translated_count += 1
            
            total_blocks_translated += translated_count
        
        # 5. Rate limiting: Add delay between pages (except after the last page)
        if page_idx < len(pages_to_process) - 1:
            time.sleep(3)  # Reduced from 5s to 3s for better UX

    # Save output
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    # Final report
    print(f"\n{'='*60}")
    print(f"📊 Translation Summary:")
    print(f"  ✅ Total blocks processed: {total_blocks_processed}")
    print(f"  ✅ Total blocks translated: {total_blocks_translated}")
    print(f"  📄 Pages processed: {len(pages_to_process)}")
    
    if failed_pages:
        print(f"  ⚠️  Failed pages: {failed_pages}")
        print(f"  ❌ Translation PARTIALLY completed (some pages failed)")
        success = False
    else:
        print(f"  ✅ All pages translated successfully!")
        success = True
    
    print(f"  💾 Output saved to: {output_file}")
    print(f"{'='*60}\n")
    
    return success

if __name__ == "__main__":
    # Check for test mode flag
    import sys
    test_mode = "--test" in sys.argv or "-t" in sys.argv
    
    if test_mode:
        print("\n🧪 Running in TEST MODE - processing first page only\n")
        success = main(test_mode=True)
    else:
        success = main()
    
    sys.exit(0 if success else 1)

