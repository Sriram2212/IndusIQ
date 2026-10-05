from backend.parsers.pdf_parser import PDFParser
from backend.parsers.docx_parser import DocxParser
from backend.parsers.excel_parser import ExcelParser
from backend.parsers.image_parser import ImageParser
from backend.utils.helpers import detect_file_type, clean_text


class IngestionAgent:
    """
    Agent 1 — Document Ingestion.
    Routes each incoming document to the correct parser based on
    file type, then cleans and returns machine-readable text.
    """

    def __init__(self):

        self.pdf_parser = PDFParser()
        self.docx_parser = DocxParser()
        self.excel_parser = ExcelParser()
        self.image_parser = ImageParser()

    def ingest(self, file_path: str) -> list:
        """
        Ingest a document file by detecting its type and
        routing to the appropriate parser.

        Returns list of page dicts with text and metadata.
        """

        file_type = detect_file_type(file_path)

        print(f"\n[DOC] Ingestion Agent — Detected type: {file_type}")
        print(f"   File: {file_path}")

        if file_type == 'pdf':
            pages = self.pdf_parser.extract_text(file_path)

        elif file_type == 'docx':
            pages = self.docx_parser.extract_text(file_path)

        elif file_type == 'excel':
            pages = self.excel_parser.extract_text(file_path)

        elif file_type == 'image':
            pages = self.image_parser.extract_text(file_path)

        else:
            print(f"   [WARNING] Unsupported file type: {file_type}")
            return []

        # Clean the text in each page
        cleaned_pages = []
        for page in pages:
            cleaned_text = clean_text(page["text"])
            cleaned_pages.append({
                "text": cleaned_text,
                "metadata": page["metadata"]
            })

        print(f"   [OK] Extracted {len(cleaned_pages)} pages/sheets")

        return cleaned_pages