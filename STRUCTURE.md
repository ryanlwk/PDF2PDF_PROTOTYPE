# PDF2PDF Prototype - Project Structure

## 📁 File Overview

```
pdf2pdf-prototype/
├── app.py                 # Main Streamlit application (3-step wizard)
├── models.py              # Pydantic data models
├── backend_mock.py        # Mock backend functions (simulates AI agents)
├── requirements.txt       # Python dependencies
├── test_models.py         # Test script to verify setup
├── run.sh                 # Quick start script
├── README.md              # Project documentation
├── STRUCTURE.md           # This file
├── .gitignore            # Git ignore patterns
├── .cursorrules          # Project-specific AI rules
└── venv/                 # Virtual environment (not tracked)
```

## 🎯 Core Files Explained

### `app.py` (Main Application)
The heart of the prototype. Contains:
- **Session State Management**: Tracks wizard progress
- **Step 1 - Upload**: File upload interface
- **Step 2 - Configuration**: Translation settings form
- **Step 3 - Workspace**: Split-view with chat interface
- **Custom CSS**: Modern UI styling
- **Routing Logic**: Navigation between steps

**Key Features:**
- Wide layout (`st.set_page_config(layout="wide")`)
- Three-column workspace (Original | Translated | Chat)
- Real-time chat interaction
- Block-based PDF display

### `models.py` (Data Models)
Pydantic models for type safety:
- **`JobConfig`**: Translation job configuration
  - target_language: str
  - glossary: GlossaryType (enum)
  - layout_priority: LayoutPriority (enum)
  - source_filename: Optional[str]

- **`PDFBlock`**: Individual translatable block
  - block_id: int
  - original_text: str
  - translated_text: str
  - position: Dict (x, y, width, height)
  - block_type: str

- **`ProcessResult`**: PDF processing results
  - original_pdf_path: str
  - translated_pdf_path: Optional[str]
  - blocks: List[PDFBlock]
  - status: str
  - error_message: Optional[str]

- **`ChatMessage`**: Chat interface messages
  - role: str (user/assistant)
  - content: str
  - timestamp: Optional[str]

### `backend_mock.py` (Mock Backend)
Simulates AI agent processing:

**Functions:**
- `mock_parse_pdf()`: Simulates PDF parsing (~2s delay)
  - Returns ProcessResult with 4 sample blocks
  - Creates original and translated text pairs

- `mock_process_chat_command()`: Processes chat commands (~1.5s delay)
  - "Make block #X shorter" → Reduces text length
  - "Make tone formal" → Adjusts formality
  - "Highlight terms" → Applies formatting
  - Returns response message and updated blocks

- `get_sample_chat_history()`: Returns demo chat messages

## 🔄 User Flow

```
┌─────────────────┐
│  Step 1: Upload │
│  - Drop PDF     │
│  - Validate     │
└────────┬────────┘
         │
         ▼
┌─────────────────────────┐
│  Step 2: Configuration  │
│  - Target Language      │
│  - Glossary Selection   │
│  - Layout Priority      │
└────────┬────────────────┘
         │
         ▼
┌──────────────────────────────────────────┐
│  Step 3: Workspace                       │
│  ┌──────────┬──────────┬──────────────┐ │
│  │ Original │Translated│ Chat         │ │
│  │ PDF      │ PDF      │ Assistant    │ │
│  │          │          │              │ │
│  │ Block #1 │ Block #1 │ 💬 Messages │ │
│  │ Block #2 │ Block #2 │              │ │
│  │ Block #3 │ Block #3 │ 📝 Input    │ │
│  │ Block #4 │ Block #4 │              │ │
│  └──────────┴──────────┴──────────────┘ │
│                                          │
│  [💾 Export] [📊 Report] [🔄 New]       │
└──────────────────────────────────────────┘
```

## 🎨 UI Components

### Header
- Gradient purple background
- Centered title and tagline

### Step Indicator
- Visual progress: 📤 Upload → ⚙️ Configure → 🚀 Workspace
- Active step highlighted in purple

### Upload Zone
- Dashed border
- Drag-and-drop support
- File validation

### Configuration Form
- Two-column layout
- Dropdowns for language and glossary
- Radio buttons for layout priority
- Info tooltip

### Workspace
- **Left Column (4 units)**: Original PDF blocks
- **Center Column (4 units)**: Translated PDF blocks
- **Right Column (3 units)**: Chat interface
- Each block has:
  - Block ID badge
  - Block type label
  - Content text
  - Left border accent

### Chat Interface
- Scrollable message container (500px height)
- User/assistant message bubbles
- Input box at bottom
- Real-time updates

## 🧪 Testing

Run tests before starting:
```bash
python3 test_models.py
```

Tests verify:
- ✅ All models instantiate correctly
- ✅ Mock backend functions work
- ✅ Timing delays are appropriate
- ✅ Data structures are valid

## 🚀 Running the App

### Option 1: Quick Start Script
```bash
./run.sh
```

### Option 2: Manual Start
```bash
source venv/bin/activate
streamlit run app.py
```

### Option 3: Direct Python
```bash
python3 -m streamlit run app.py
```

## 📊 Sample Data

The prototype includes 4 mock PDF blocks:
1. **Heading**: "Welcome to Our Annual Report"
2. **Text**: Company performance overview
3. **Heading**: "Financial Highlights"
4. **Text**: Revenue growth details

All blocks have:
- Original English text
- Spanish translation
- Position coordinates
- Block type classification

## 🎯 Design Decisions

### Why Streamlit?
- Rapid prototyping
- Python-native
- Built-in state management
- Easy deployment

### Why Pydantic?
- Type safety
- Data validation
- Clear data contracts
- IDE autocomplete support

### Why Mock Backend?
- Phase 1 focus on UX
- No external dependencies
- Predictable behavior
- Fast iteration

### Why Block-Based Display?
- Clear reference points for chat
- Easy to identify sections
- Supports future editing
- Mimics real PDF structure

## 🔮 Future Enhancements

### Phase 2: Real Processing
- PDF parsing library (PyMuPDF/pdfplumber)
- Translation API integration (OpenAI/DeepL)
- PDF rendering (pdf2image)

### Phase 3: Advanced Features
- Multi-page support
- Image translation
- Table preservation
- Export formats (DOCX, HTML)

### Phase 4: Production
- User authentication
- Project management
- Collaboration features
- API access

## 💡 Key Takeaways

1. **Session State**: Critical for wizard flow
2. **Mock Data**: Enables rapid UX testing
3. **Type Safety**: Pydantic prevents bugs
4. **Visual Hierarchy**: Clear step progression
5. **Interactive Chat**: The "wow" factor

---

**Built for**: High-fidelity UI demonstration  
**Phase**: 1 (Prototype)  
**Focus**: UX flow and interaction patterns  
**Tech**: Streamlit + Pydantic + Python 3.10+


