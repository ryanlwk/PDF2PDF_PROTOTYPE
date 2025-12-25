# PDF2PDF Prototype

A high-fidelity UI mockup demonstrating the "Chat & Modify" workflow for intelligent PDF translation.

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- Virtual environment (already set up in `venv/`)

### Installation

1. Activate the virtual environment:
```bash
source venv/bin/activate
```

2. Install dependencies (if not already installed):
```bash
pip install -r requirements.txt
```

### Running the Application

```bash
streamlit run app.py
```

The application will open in your default browser at `http://localhost:8501`

## 📋 Features

### 3-Step Wizard Workflow

#### Step 1: Upload
- Clean, centered drop zone for PDF upload
- File validation
- Smooth transition to configuration

#### Step 2: Configuration
- **Target Language Selection**: Choose from Spanish, French, German, Chinese, Japanese, Portuguese
- **Glossary Selection**: None, Medical, Legal, Technical, Financial
- **Layout Priority**: Accuracy vs. Readability toggle

#### Step 3: Workspace (The "Wow" Factor)
- **Split View Layout**:
  - Left: Original PDF document
  - Center: Translated PDF document
  - Right: AI Chat Assistant
- **Interactive Chat**: Modify translations in real-time
  - "Make block #2 shorter"
  - "Make the tone more formal"
  - "Highlight key financial terms"

## 🏗️ Architecture

### Files

- **`app.py`**: Main Streamlit application with 3-step wizard
- **`models.py`**: Pydantic data models for type safety
- **`backend_mock.py`**: Mock backend functions simulating AI agents
- **`requirements.txt`**: Python dependencies

### Data Models

- `JobConfig`: Translation job configuration
- `ProcessResult`: PDF processing results
- `PDFBlock`: Individual translatable blocks
- `ChatMessage`: Chat interface messages

## 🎨 UI/UX Highlights

- **Modern Gradient Header**: Eye-catching purple gradient
- **Step Indicator**: Visual progress through the wizard
- **Block-Based Display**: Each PDF block is clearly separated and numbered
- **Real-time Chat**: Interactive AI assistant for refinements
- **Responsive Layout**: Wide layout optimized for desktop use

## 🔧 Mock Backend

The prototype uses simulated processing with realistic delays:
- PDF parsing: ~2 seconds
- Chat commands: ~1.5 seconds
- Sample blocks with original and translated text

### Supported Chat Commands

- Shorten blocks: "Make block #2 shorter"
- Tone adjustment: "Make the tone more formal"
- Formatting: "Highlight key financial terms"
- Information queries: "Tell me about the revenue section"

## 📦 Tech Stack

- **Framework**: Streamlit 1.52.2
- **Data Validation**: Pydantic 2.12.5
- **Language**: Python 3.10+

## 🎯 Phase Strategy

This is **Phase 1 (Prototype)** - prioritizing speed and visual demonstration.
- No real PDF processing
- No actual translation API calls
- Focus on UX flow and interaction patterns

## 🚧 Future Enhancements (Phase 2+)

- Real PDF parsing and rendering
- Integration with translation APIs
- Actual AI agent implementation
- Export functionality
- Comparison reports
- User authentication
- Project management

## 💡 Tips

- Use the chat to interact with the translated document
- Try different commands to see various AI responses
- The blocks are numbered for easy reference
- Layout priority affects how the translation is optimized

---

Built with ❤️ using Streamlit


