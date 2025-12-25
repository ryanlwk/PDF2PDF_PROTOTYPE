"""
Mock backend functions to simulate PDF processing and AI agents.
"""
import time
import asyncio
from typing import List
from models import ProcessResult, PDFBlock, ChatMessage, JobConfig


def mock_parse_pdf(file_path: str, config: JobConfig) -> ProcessResult:
    """
    Simulate PDF parsing with a delay.
    Returns a ProcessResult with mock blocks.
    """
    time.sleep(2)  # Simulate processing time
    
    # Create mock blocks
    mock_blocks = [
        PDFBlock(
            block_id=1,
            original_text="Welcome to Our Annual Report",
            translated_text="Bienvenido a Nuestro Informe Anual",
            position={"x": 100, "y": 100, "width": 400, "height": 50},
            block_type="heading"
        ),
        PDFBlock(
            block_id=2,
            original_text="This document provides a comprehensive overview of our company's performance in 2024. We have achieved significant milestones and continue to grow our market presence.",
            translated_text="Este documento proporciona una visión integral del desempeño de nuestra empresa en 2024. Hemos logrado hitos significativos y continuamos creciendo nuestra presencia en el mercado.",
            position={"x": 100, "y": 180, "width": 400, "height": 100},
            block_type="text"
        ),
        PDFBlock(
            block_id=3,
            original_text="Financial Highlights",
            translated_text="Aspectos Financieros Destacados",
            position={"x": 100, "y": 300, "width": 400, "height": 40},
            block_type="heading"
        ),
        PDFBlock(
            block_id=4,
            original_text="Revenue increased by 25% year-over-year, reaching $50 million. Our operational efficiency improvements have contributed significantly to this growth.",
            translated_text="Los ingresos aumentaron un 25% interanual, alcanzando los $50 millones. Las mejoras en nuestra eficiencia operativa han contribuido significativamente a este crecimiento.",
            position={"x": 100, "y": 360, "width": 400, "height": 80},
            block_type="text"
        ),
    ]
    
    return ProcessResult(
        original_pdf_path=file_path,
        translated_pdf_path="/mock/translated.pdf",
        blocks=mock_blocks,
        status="completed"
    )


async def mock_translate_async(config: JobConfig) -> str:
    """Async version of translation simulation."""
    await asyncio.sleep(2)
    return f"Translation to {config.target_language} completed!"


def mock_process_chat_command(command: str, blocks: List[PDFBlock]) -> tuple[str, List[PDFBlock]]:
    """
    Simulate processing a chat command.
    Returns: (response_message, updated_blocks)
    """
    time.sleep(1.5)  # Simulate AI thinking
    
    command_lower = command.lower()
    
    if "shorter" in command_lower and "block" in command_lower:
        # Extract block number if mentioned
        block_num = None
        for word in command.split():
            if word.startswith("#"):
                try:
                    block_num = int(word[1:])
                except ValueError:
                    pass
        
        if block_num and 0 < block_num <= len(blocks):
            # Shorten the specified block
            block = blocks[block_num - 1]
            original_length = len(block.translated_text)
            block.translated_text = block.translated_text[:len(block.translated_text)//2] + "..."
            return f"✅ Made block #{block_num} shorter (reduced from {original_length} to {len(block.translated_text)} characters)", blocks
        else:
            return "❌ Could not identify which block to shorten. Please specify like 'Make block #2 shorter'", blocks
    
    elif "formal" in command_lower or "professional" in command_lower:
        # Make all text more formal
        for block in blocks:
            if block.block_type == "text":
                block.translated_text = block.translated_text.replace("hemos", "la empresa ha")
        return "✅ Adjusted tone to be more formal across all text blocks", blocks
    
    elif "highlight" in command_lower or "bold" in command_lower:
        return "✅ Applied bold formatting to key financial terms", blocks
    
    elif "revenue" in command_lower or "financial" in command_lower:
        return "📊 The financial section is in blocks #3 and #4. Revenue data shows 25% YoY growth to $50M.", blocks
    
    else:
        return "🤖 I can help you modify the translation! Try commands like:\n- 'Make block #2 shorter'\n- 'Make the tone more formal'\n- 'Highlight key financial terms'", blocks


def get_sample_chat_history() -> List[ChatMessage]:
    """Return sample chat history for demo purposes."""
    return [
        ChatMessage(
            role="assistant",
            content="👋 Hello! I'm your PDF translation assistant. The document has been translated. How can I help you refine it?"
        ),
        ChatMessage(
            role="user",
            content="Can you make the introduction shorter?"
        ),
        ChatMessage(
            role="assistant",
            content="✅ I've condensed the introduction in block #2 to be more concise while retaining key information."
        ),
    ]


