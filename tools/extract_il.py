import hashlib
import json
import os
import sys
from typing import List, Dict, Any

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from pdfminer.high_level import extract_pages
from pdfminer.layout import (
    LTPage, LTTextContainer, LTFigure, LTImage, LTChar, LAParams
)
try:
    from PIL import Image
    import io
except ImportError:
    print("⚠️ PIL (Pillow) not found. Image extraction will be skipped.")
    Image = None

from models import DocumentIL, PageIL, BlockIL, BlockType

def generate_block_id(page_idx: int, bbox: tuple) -> str:
    """Generate stable Hash ID"""
    raw = f"{page_idx}-{bbox[0]:.2f}-{bbox[1]:.2f}-{bbox[2]:.2f}-{bbox[3]:.2f}"
    return hashlib.md5(raw.encode()).hexdigest()[:8]

class PDFParser:
    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        self.asset_dir = os.path.join(os.path.dirname(pdf_path), "assets")
        
        if not os.path.exists(self.asset_dir):
            os.makedirs(self.asset_dir)

        # Custom LAParams (Geometry-First Strategy)
        self.laparams = LAParams(
            line_overlap=0.5,
            char_margin=2.0,
            line_margin=0.5,
            word_margin=0.1,
            boxes_flow=0.5, 
            detect_vertical=False,
            all_texts=False  # Manual recursion for Figures
        )

    def parse(self) -> DocumentIL:
        print(f"🔍 Parsing {self.pdf_path}...")
        pages_il = []
        
        for page_idx, page_layout in enumerate(extract_pages(self.pdf_path, laparams=self.laparams)):
            print(f"  - Processing Page {page_idx + 1}...")
            blocks = self._parse_page(page_idx, page_layout)
            
            pages_il.append(PageIL(
                page_index=page_idx,
                width=page_layout.width,
                height=page_layout.height,
                blocks=blocks
            ))

        return DocumentIL(
            filename=os.path.basename(self.pdf_path),
            total_pages=len(pages_il),
            pages=pages_il
        )

    def _parse_page(self, page_idx: int, layout: LTPage) -> List[BlockIL]:
        blocks = []
        for element in layout:
            parsed_block = self._process_element(page_idx, element)
            if parsed_block:
                blocks.append(parsed_block)
        return blocks

    def _process_element(self, page_idx: int, element) -> BlockIL | None:
        bbox = (element.x0, element.y0, element.x1, element.y1)
        block_id = generate_block_id(page_idx, bbox)

        # 1. Text Container
        if isinstance(element, LTTextContainer):
            text = element.get_text().strip()
            if not text: return None
            return BlockIL(
                id=block_id, type=BlockType.BODY, bbox=list(bbox), content=text
            )

        # 2. Chart/Figure (Recursive)
        elif isinstance(element, LTFigure):
            return self._handle_figure(page_idx, element, block_id, bbox)

        # 3. Pure Image (LTImage)
        elif isinstance(element, LTImage):
            img_path = self._save_image(element, page_idx, block_id)
            return BlockIL(
                id=block_id, type=BlockType.IMAGE, bbox=list(bbox), 
                content="[IMAGE]", metadata={"image_path": img_path}
            )
            
        return None

    def _handle_figure(self, page_idx: int, figure: LTFigure, block_id: str, bbox: tuple) -> BlockIL:
        """Atomic Grouping Logic + Coordinate Recording"""
        inner_texts = []
        inner_images = []
        
        def extract_inner(obj):
            if isinstance(obj, (LTTextContainer, LTChar)):
                if hasattr(obj, 'get_text'):
                    txt = obj.get_text().strip()
                    if txt:
                        # Record relative coordinates for Phase 4 rendering
                        inner_texts.append({
                            "text": txt,
                            "bbox": [obj.x0, obj.y0, obj.x1, obj.y1] 
                        })
            elif isinstance(obj, LTImage):
                inner_images.append(obj)
            elif isinstance(obj, LTFigure):
                for child in obj: extract_inner(child)

        for child in figure: extract_inner(child)

        if inner_texts:
            # Type: CHART (Atomic Chart with text)
            bg_img_path = None
            if inner_images:
                bg_img_path = self._save_image(inner_images[0], page_idx, block_id + "_bg")

            content_str = " ".join([t["text"] for t in inner_texts])
            return BlockIL(
                id=block_id,
                type=BlockType.CHART,
                bbox=list(bbox),
                content=content_str,
                metadata={
                    "is_atomic": True,
                    "chart_text_blocks": inner_texts,
                    "background_image": bg_img_path
                }
            )
        else:
            # Type: IMAGE (Vector Art or Container)
            img_path = None
            if inner_images:
                img_path = self._save_image(inner_images[0], page_idx, block_id)
            
            return BlockIL(
                id=block_id,
                type=BlockType.IMAGE,
                bbox=list(bbox),
                content="[VECTOR/IMAGE]",
                metadata={"image_path": img_path}
            )

    def _save_image(self, lt_image: LTImage, page_idx: int, block_id: str) -> str | None:
        """Extract and save image from PDF stream"""
        if not Image: return None
        try:
            if lt_image.stream:
                file_ext = ".jpg"
                filters = lt_image.stream.get_filters()
                if filters:
                    if 'FlateDecode' in filters: file_ext = ".png"
                    elif 'DCTDecode' in filters: file_ext = ".jpg"
                    elif 'JPXDecode' in filters: file_ext = ".jp2"
                
                filename = f"p{page_idx+1}_{block_id}{file_ext}"
                filepath = os.path.join(self.asset_dir, filename)
                
                with open(filepath, "wb") as f:
                    f.write(lt_image.stream.get_rawdata())
                return os.path.join("assets", filename)
        except Exception as e:
            print(f"⚠️ Failed to save image {block_id}: {e}")
            return None
        return None

if __name__ == "__main__":
    input_pdf = "somatosensory.pdf"
    
    if not os.path.exists(input_pdf):
        print(f"❌ Error: {input_pdf} not found.")
        sys.exit(1)

    parser = PDFParser(input_pdf)
    doc_il = parser.parse()
    
    with open("intermediate_layer.json", "w", encoding="utf-8") as f:
        f.write(doc_il.model_dump_json(indent=2))
        
    print(f"✅ Output saved to intermediate_layer.json")

