"""
Quick test script to verify models and backend mock functions.
Run this to ensure everything is working before starting the Streamlit app.
"""
from models import JobConfig, ProcessResult, PDFBlock, ChatMessage, GlossaryType, LayoutPriority
from backend_mock import mock_parse_pdf, mock_process_chat_command, get_sample_chat_history


def test_models():
    """Test that all models can be instantiated correctly."""
    print("Testing models...")
    
    # Test JobConfig
    config = JobConfig(
        target_language="Spanish",
        glossary=GlossaryType.MEDICAL,
        layout_priority=LayoutPriority.ACCURACY,
        source_filename="test.pdf"
    )
    print(f"✅ JobConfig created: {config.target_language}")
    
    # Test PDFBlock
    block = PDFBlock(
        block_id=1,
        original_text="Hello",
        translated_text="Hola",
        position={"x": 0, "y": 0, "width": 100, "height": 50}
    )
    print(f"✅ PDFBlock created: Block #{block.block_id}")
    
    # Test ChatMessage
    message = ChatMessage(role="user", content="Test message")
    print(f"✅ ChatMessage created: {message.role}")
    
    print("\n✅ All models working correctly!\n")


def test_backend_mock():
    """Test backend mock functions."""
    print("Testing backend mock functions...")
    
    # Test mock_parse_pdf
    config = JobConfig(
        target_language="Spanish",
        glossary=GlossaryType.NONE,
        layout_priority=LayoutPriority.ACCURACY
    )
    
    print("⏳ Testing mock_parse_pdf (this will take ~2 seconds)...")
    result = mock_parse_pdf("test.pdf", config)
    print(f"✅ PDF parsed: {len(result.blocks)} blocks created")
    print(f"   Status: {result.status}")
    
    # Test mock_process_chat_command
    print("\n⏳ Testing mock_process_chat_command...")
    response, updated_blocks = mock_process_chat_command(
        "Make block #2 shorter",
        result.blocks
    )
    print(f"✅ Chat command processed")
    print(f"   Response: {response[:50]}...")
    
    # Test get_sample_chat_history
    history = get_sample_chat_history()
    print(f"\n✅ Sample chat history: {len(history)} messages")
    
    print("\n✅ All backend mock functions working correctly!\n")


def main():
    """Run all tests."""
    print("=" * 60)
    print("PDF2PDF Prototype - Model & Backend Tests")
    print("=" * 60 + "\n")
    
    try:
        test_models()
        test_backend_mock()
        
        print("=" * 60)
        print("🎉 All tests passed! You're ready to run the app.")
        print("=" * 60)
        print("\nRun the app with: streamlit run app.py")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()


