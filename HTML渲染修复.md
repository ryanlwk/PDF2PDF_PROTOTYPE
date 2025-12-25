# HTML 渲染修复 🔧

## 🐛 问题描述

**症状**: PDF 显示为纯文本 `<embed src="data:application/pdf;base64...` 而不是实际的 PDF 查看器

**原因**: `st.markdown(html, unsafe_allow_html=True)` 在某些情况下不能正确渲染 `<embed>` 或 `<iframe>` 标签

---

## ✅ 解决方案

### 修改前（不工作）

```python
def display_native_pdf(file_path, height=700):
    # ... 读取文件 ...
    
    pdf_display = f"""
        <embed src="data:application/pdf;base64,{base64_pdf}" ...>
    """
    
    # ❌ 问题：有时显示为纯文本
    st.markdown(pdf_display, unsafe_allow_html=True)
```

### 修改后（工作）

```python
def display_native_pdf(file_path, height=700):
    # ... 读取文件 ...
    
    pdf_display = f"""
        <iframe src="data:application/pdf;base64,{base64_pdf}" ...></iframe>
    """
    
    # ✅ 解决：使用 st.components.v1.html()
    import streamlit.components.v1 as components
    components.html(pdf_display, height=height, scrolling=True)
```

---

## 🔑 关键改动

### 1. 从 embed 改为 iframe

```html
<!-- 之前 -->
<embed src="..." width="100%" height="700px">

<!-- 现在 -->
<iframe src="..." width="100%" height="700px"></iframe>
```

**理由**: `<iframe>` 更标准，浏览器支持更好

### 2. 使用 st.components.v1.html()

```python
# 之前
st.markdown(html, unsafe_allow_html=True)

# 现在  
import streamlit.components.v1 as components
components.html(html, height=height, scrolling=True)
```

**理由**: `components.html()` 专门用于渲染自定义 HTML，比 `st.markdown()` 更可靠

---

## 🚀 如何测试修复

### 1. 重启应用

```bash
# 停止当前运行（Ctrl+C）
# 重新启动
streamlit run app.py
```

### 2. 检查 PDF 显示

- [ ] 左栏显示原始 PDF（不是文本）
- [ ] 中栏显示翻译 PDF（不是文本）
- [ ] PDF 可以滚动和缩放
- [ ] 无 embed/iframe 文本可见

---

## 📊 st.markdown vs st.components.html

| 特性 | st.markdown | st.components.html |
|------|------------|-------------------|
| **用途** | 渲染 Markdown + HTML | 渲染自定义 HTML/JS |
| **embed 支持** | ⚠️ 不可靠 | ✅ 可靠 |
| **iframe 支持** | ⚠️ 不可靠 | ✅ 可靠 |
| **自定义高度** | ❌ 受限 | ✅ 完全控制 |
| **推荐用于 PDF** | ❌ 不推荐 | ✅ 推荐 |

---

## 💡 为什么 st.markdown 不工作？

### Streamlit 的安全限制

Streamlit 对 `st.markdown()` 中的 HTML 有严格的安全过滤：

1. **移除某些标签**: `<embed>`, `<object>`, `<iframe>` 等可能被过滤
2. **转义特殊字符**: 某些情况下 HTML 被转义为纯文本
3. **限制 data URI**: `data:application/pdf` 可能被阻止

### st.components.html() 的优势

1. **专用 HTML 渲染器**: 设计用于自定义组件
2. **完整 HTML 支持**: 不过滤标签
3. **独立沙盒**: 在 iframe 中渲染，安全隔离
4. **精确控制**: 可以设置 height, scrolling 等参数

---

## 🔍 常见问题

### Q: 为什么改用 iframe 而不是 embed？

**A**: 
- `<iframe>` 是 HTML5 标准
- 更好的浏览器兼容性
- `st.components.html()` 对 iframe 支持更好

### Q: scrolling=True 的作用？

**A**: 允许 iframe 内容滚动，确保多页 PDF 可以查看

### Q: 还是不显示 PDF？

**A**: 检查以下几点：
1. 浏览器控制台是否有错误
2. PDF 文件是否存在
3. Base64 编码是否正确
4. 浏览器是否支持 PDF（Chrome/Edge/Firefox）

---

## 📝 完整修复后的代码

```python
def display_native_pdf(file_path, height=700):
    """
    使用 <iframe> 標籤顯示 PDF。
    通過 st.components.html() 確保正確渲染。
    """
    if not os.path.exists(file_path):
        st.error(f"📄 File not found: {file_path}")
        return

    with open(file_path, "rb") as f:
        base64_pdf = base64.b64encode(f.read()).decode('utf-8')

    # 使用 iframe，比 embed 更可靠
    pdf_display = f"""
        <iframe
            src="data:application/pdf;base64,{base64_pdf}"
            width="100%"
            height="{height}px"
            type="application/pdf"
            style="border: 1px solid #ddd; border-radius: 5px;"
        ></iframe>
    """
    
    # 使用 st.components.v1.html 确保 HTML 正确渲染
    import streamlit.components.v1 as components
    components.html(pdf_display, height=height, scrolling=True)
```

---

## ✅ 测试清单

修复后应该看到：

- [ ] ✅ PDF 正常显示（不是文本代码）
- [ ] ✅ 左右两栏都显示 PDF
- [ ] ✅ 可以滚动查看多页
- [ ] ✅ PDF 填满容器宽度
- [ ] ✅ 聊天功能正常

---

## 🎉 总结

### 修复要点

1. **从 embed 改为 iframe** - 更标准、更可靠
2. **使用 st.components.html()** - 专门的 HTML 渲染器
3. **添加 scrolling=True** - 支持多页滚动

### 为什么这次能成功

- ✅ `st.components.html()` 不会过滤 HTML 标签
- ✅ `<iframe>` 有更好的浏览器支持
- ✅ 独立沙盒环境，避免冲突

---

**修复状态**: ✅ 完成  
**测试**: ⏳ 请重启应用测试  

**重启命令**: `streamlit run app.py` 🚀

