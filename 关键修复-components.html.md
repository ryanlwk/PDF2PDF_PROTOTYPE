# 关键修复：为什么必须用 st.components.v1.html() ✅

## 🐛 问题根源

### 症状
翻译后的 PDF（output_tc.pdf）在 `<h6>🌍 Translated (zh-HK)</h6>` 下方**完全不显示**

### 错误的代码（不工作）

```python
def display_pdf(file_path, height=700):
    # ... Base64 编码 ...
    
    pdf_display = f"""
        <iframe src="data:application/pdf;base64,{base64_pdf}"...>
        </iframe>
    """
    
    # ❌ 错误：st.markdown() 会过滤掉 iframe！
    st.markdown(pdf_display, unsafe_allow_html=True)
```

### 为什么不工作？

**关键问题**: `st.markdown(html, unsafe_allow_html=True)` **会过滤某些 HTML 标签**！

Streamlit 的安全机制会：
1. **移除 `<iframe>` 标签** - 防止 XSS 攻击
2. **移除 `<embed>` 标签** - 同样的安全原因
3. **移除 `<object>` 标签** - 安全过滤
4. **转义或删除** 其他"危险"的 HTML

结果：你的 iframe 被**完全删除**，PDF 无法显示！

---

## ✅ 正确的解决方案

### 使用 st.components.v1.html()

```python
def display_pdf(file_path, height=700):
    # ... Base64 编码 ...
    
    pdf_display = f"""
        <iframe src="data:application/pdf;base64,{base64_pdf}"...>
        </iframe>
    """
    
    # ✅ 正确：st.components.v1.html() 不会过滤 HTML
    import streamlit.components.v1 as components
    components.html(pdf_display, height=height + 10, scrolling=False)
```

---

## 📊 st.markdown vs st.components.html

| 特性 | st.markdown | st.components.html |
|------|------------|-------------------|
| **用途** | 显示 Markdown + 安全 HTML | 渲染自定义 HTML/JS 组件 |
| **安全过滤** | ✅ 严格（会删除 iframe） | ❌ 无过滤（你负责安全） |
| **iframe 支持** | ❌ **被过滤** | ✅ **完全支持** |
| **embed 支持** | ❌ **被过滤** | ✅ **完全支持** |
| **PDF 显示** | ❌ **不适合** | ✅ **推荐** |
| **自定义高度** | ⚠️ 有限 | ✅ 精确控制 |

---

## 🔍 验证修复

### 如何确认 iframe 被过滤了？

1. **查看浏览器 DevTools**:
   - 打开浏览器开发者工具（F12）
   - 切换到 Elements/检查元素 标签页
   - 搜索 `iframe`
   - 如果找不到 → 被过滤了！

2. **查看源代码**:
   - 右键点击空白区域 → 查看页面源代码
   - 搜索 `data:application/pdf`
   - 如果找不到 → 被删除了！

---

## 🚀 应用修复

### 步骤 1: 停止应用

在终端按 **Ctrl+C**

### 步骤 2: 重启应用

```bash
streamlit run app.py
```

### 步骤 3: 验证显示

现在应该看到：

- ✅ **左栏**: somatosensory.pdf 正常显示
- ✅ **中栏**: output_tc.pdf **正常显示**（之前不显示）
- ✅ **两个 PDF** 都可以滚动、缩放
- ✅ 无空白、无错误

---

## 💡 为什么 components.html() 能工作？

### 工作原理

```
st.components.v1.html()
    ↓
创建一个独立的 iframe 容器
    ↓
在这个 iframe 中渲染你的 HTML
    ↓
不经过 Streamlit 的安全过滤
    ↓
你的 iframe（包含 PDF）正常显示 ✅
```

### 安全考虑

- `components.html()` **不过滤** HTML
- 这意味着**你要负责安全性**
- 在这个案例中安全：我们控制所有输入（本地 PDF 文件）
- 不要用于用户提交的不受信任的 HTML！

---

## 🔧 完整修复后的代码

```python
def display_pdf(file_path, height=700):
    """
    使用 <iframe> 標籤顯示 PDF。
    
    關鍵修正：
    1. 使用 st.components.v1.html() 而非 st.markdown()
    2. st.markdown() 會過濾 iframe 標籤！
    3. components.html() 不會過濾，能正確渲染
    """
    if not os.path.exists(file_path):
        st.error(f"📄 File not found: {file_path}")
        return

    try:
        with open(file_path, "rb") as f:
            base64_pdf = base64.b64encode(f.read()).decode('utf-8')

        pdf_display = f"""
            <iframe 
                src="data:application/pdf;base64,{base64_pdf}" 
                width="100%" 
                height="{height}px" 
                style="border: 1px solid #ddd; border-radius: 5px;">
            </iframe>
        """
        
        # 使用 components.html() 确保 iframe 不被过滤
        import streamlit.components.v1 as components
        components.html(pdf_display, height=height + 10, scrolling=False)
        
    except Exception as e:
        st.error(f"Error loading PDF: {str(e)}")
```

---

## ✅ 测试清单

修复后验证：

- [ ] ✅ 左栏显示 somatosensory.pdf
- [ ] ✅ **中栏显示 output_tc.pdf**（之前空白）
- [ ] ✅ 两个 PDF 都可以滚动
- [ ] ✅ 两个 PDF 都有浏览器工具栏
- [ ] ✅ 右侧聊天正常
- [ ] ✅ 无错误消息

---

## 🎓 学到的教训

### 关键要点

1. **st.markdown() 不适合 iframe**
   - 即使有 `unsafe_allow_html=True`
   - 会被安全过滤删除

2. **使用 st.components.v1.html()**
   - 专门用于自定义 HTML
   - 不会过滤标签
   - 是显示 PDF 的正确方法

3. **为什么文档没说清楚？**
   - Streamlit 文档假设你知道安全过滤
   - `unsafe_allow_html=True` 只是"部分"unsafe
   - 仍然有白名单机制

---

## 📝 参数说明

### components.html() 参数

```python
components.html(
    html,                    # HTML 字符串
    height=height + 10,      # 容器高度（像素）
    scrolling=False          # 是否显示滚动条
)
```

**为什么 height + 10？**
- 给容器留一点额外空间
- 避免不必要的滚动条
- 视觉上更整洁

**为什么 scrolling=False？**
- PDF 自己有滚动条
- 不需要外部容器的滚动条
- 避免双重滚动条

---

## 🔍 如果还是不显示？

### 调试步骤

1. **检查浏览器控制台**:
   ```
   F12 → Console 标签页
   查看是否有错误消息
   ```

2. **检查文件是否存在**:
   ```bash
   ls -la output_tc.pdf
   # 应该看到文件
   ```

3. **检查文件大小**:
   ```bash
   du -h output_tc.pdf
   # 如果超过 10MB，Base64 可能会有问题
   ```

4. **尝试小文件测试**:
   - 用一个小 PDF（< 1MB）测试
   - 如果小文件显示，说明是大文件问题

---

## 🎉 总结

### 问题
- `st.markdown(iframe_html, unsafe_allow_html=True)` **删除 iframe**
- 导致 PDF 完全不显示

### 解决方案
- 使用 `st.components.v1.html(iframe_html, ...)`
- 不会过滤 HTML，iframe 正常显示

### 关键教训
- **不要用 st.markdown() 显示 iframe/embed**
- **必须用 st.components.v1.html()**

---

**修复状态**: ✅ 完成  
**需要重启**: ✅ 是（Ctrl+C 然后 streamlit run app.py）  
**预期结果**: output_tc.pdf 在中栏正常显示  

**立即重启测试！** 🚀

