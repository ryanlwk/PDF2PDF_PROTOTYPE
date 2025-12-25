"""
Pydantic models for PDF2PDF application data structures.
"""
from typing import Optional, List, Dict
from pydantic import BaseModel, Field
from enum import Enum


class LayoutPriority(str, Enum):
    """Layout priority options."""
    ACCURACY = "accuracy"
    READABILITY = "readability"


class GlossaryType(str, Enum):
    """Available glossary types."""
    NONE = "None"
    MEDICAL = "Medical"
    LEGAL = "Legal"
    TECHNICAL = "Technical"
    FINANCIAL = "Financial"


class JobConfig(BaseModel):
    """Configuration for a PDF translation job."""
    target_language: str = Field(..., description="Target language for translation")
    glossary: GlossaryType = Field(default=GlossaryType.NONE, description="Glossary to use")
    layout_priority: LayoutPriority = Field(default=LayoutPriority.ACCURACY, description="Layout priority")
    source_filename: Optional[str] = Field(None, description="Original PDF filename")


class PDFBlock(BaseModel):
    """Represents a translatable block in the PDF."""
    block_id: int
    original_text: str
    translated_text: str
    position: Dict[str, float] = Field(default_factory=dict)  # x, y, width, height
    block_type: str = "text"  # text, image, table, etc.


class ProcessResult(BaseModel):
    """Result of PDF processing."""
    original_pdf_path: str
    translated_pdf_path: Optional[str] = None
    blocks: List[PDFBlock] = Field(default_factory=list)
    status: str = "pending"  # pending, processing, completed, error
    error_message: Optional[str] = None


class ChatMessage(BaseModel):
    """Chat message in the workspace."""
    role: str  # "user" or "assistant"
    content: str
    timestamp: Optional[str] = None


