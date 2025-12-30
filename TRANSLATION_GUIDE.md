# Translation Guide - PDF2PDF Prototype

## ✅ Setup Complete!

Your translation system has been updated with:
1. ✅ Better error handling and reporting
2. ✅ Test mode for quick validation
3. ✅ Detailed translation statistics
4. ✅ Working model configuration

---

## 🎯 Quick Start

### Test Translation (First Page Only)
```bash
python tools/translate_il.py --test
```

### Full Translation (All Pages)
```bash
python tools/translate_il.py
```

---

## 🤖 Available Free Models on OpenRouter

### Currently Configured (Working ✅)
```bash
OPENROUTER_MODEL=google/gemini-2.0-flash-exp:free
```
- **Status**: ✅ Tested and working
- **Best for**: General translation, reliable
- **Context**: 1M tokens

### Alternative Free Qwen Models

#### Option 1: Qwen3 Coder (Best for Technical Content)
```bash
OPENROUTER_MODEL=qwen/qwen3-coder:free
```
- **Model**: Qwen3 Coder 480B A35B
- **Best for**: Code, technical documentation
- **Context**: Large

#### Option 2: Qwen3 4B (Fastest)
```bash
OPENROUTER_MODEL=qwen/qwen3-4b:free
```
- **Model**: Qwen3 4B
- **Best for**: Quick translations, simple text
- **Speed**: Fastest

#### Option 3: Qwen 2.5 VL 7B (Vision + Text)
```bash
OPENROUTER_MODEL=qwen/qwen-2.5-vl-7b-instruct:free
```
- **Model**: Qwen2.5-VL 7B Instruct
- **Best for**: Documents with images
- **Features**: Vision + Language

### Other Reliable Free Models

```bash
# Mistral (Fast & Reliable)
OPENROUTER_MODEL=mistralai/mistral-7b-instruct:free

# Meta LLaMA (Note: Currently has issues with JSON format)
OPENROUTER_MODEL=meta-llama/llama-3.1-405b-instruct:free
```

---

## 🔧 How to Switch Models

1. **Edit `.env` file** in the project root:
   ```bash
   nano .env
   ```

2. **Update or add** the model line:
   ```bash
   OPENROUTER_MODEL=qwen/qwen3-coder:free
   ```

3. **Test the new model**:
   ```bash
   python tools/translate_il.py --test
   ```

4. **If successful, run full translation**:
   ```bash
   python tools/translate_il.py
   ```

---

## 📊 What the Script Does

### Improved Features (v2.0)

1. **Better Error Reporting**
   - Shows which pages failed
   - Provides specific error messages
   - Validates translations contain Chinese characters

2. **Test Mode**
   - Use `--test` flag to translate only first page
   - Saves to `translated_layer_test.json`
   - Quick validation before full run

3. **Translation Statistics**
   - Total blocks processed
   - Total blocks translated
   - Success/failure per page
   - Failed page numbers

4. **Smart Validation**
   - Checks if translations actually contain Chinese
   - Verifies block count matches
   - Reports mismatches

---

## 🐛 Troubleshooting

### Error: "No endpoints found for [model]"
**Solution**: Model name is incorrect or not available
```bash
# Check available models:
curl -s "https://openrouter.ai/api/v1/models" \
  -H "Authorization: Bearer YOUR_API_KEY" | \
  python3 -m json.tool | grep -A 5 "qwen"

# Or use the working Gemini model:
OPENROUTER_MODEL=google/gemini-2.0-flash-exp:free
```

### Error: "Value error" (400)
**Solution**: Model doesn't support JSON response format
- Try a different model (Gemini works well)
- Some models don't support `response_format: json_object`

### Error: Rate Limit
**Solution**: Script already has exponential backoff
- Wait between retries is automatic
- Free tier has rate limits
- Script delays 3s between pages

### Translation Not in Chinese
**Solution**: Script now validates this
- Will retry if no Chinese characters detected
- Check model supports Chinese output
- Gemini and Qwen models work well

---

## 📝 Test Results

### ✅ Successful Test (Dec 26, 2025)

**Model**: `google/gemini-2.0-flash-exp:free`

**Results**:
- ✅ 22 blocks translated
- ✅ All translations in Traditional Chinese (Hong Kong)
- ✅ Processing time: ~7 seconds for 1 page
- ✅ Output: `translated_layer_test.json`

**Sample Translation**:
```
Original: "Anatomy of the Somatosensory System"
Translated: "體感覺系統的解剖學"
```

---

## 🎓 Best Practices

1. **Always test first**
   ```bash
   python tools/translate_il.py --test
   ```

2. **Check the test output**
   ```bash
   # Look for Chinese characters in the output
   head -50 translated_layer_test.json
   ```

3. **Monitor during full translation**
   - Watch for error messages
   - Check success rate per page
   - Review final statistics

4. **If a page fails**
   - Script continues with other pages
   - Failed pages listed at the end
   - Can retry just those pages if needed

---

## 📂 Output Files

- `intermediate_layer.json` - Input (English)
- `translated_layer_test.json` - Test output (first page)
- `translated_layer.json` - Full output (all pages)

---

## 🚀 Next Steps

1. ✅ Test mode works with Gemini
2. 🔄 Try Qwen models if desired
3. ▶️ Run full translation when ready
4. ✅ Verify output in Streamlit app

---

## 💡 Tips

- **Gemini** is most reliable for general translation
- **Qwen3 Coder** is best for technical/code content
- **Qwen3 4B** is fastest but may be less accurate
- Always run `--test` before full translation
- Check API key is valid if getting auth errors

---

*Last Updated: Dec 26, 2025*
*Script Version: 2.0 (Enhanced Error Handling)*

