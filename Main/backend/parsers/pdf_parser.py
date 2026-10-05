try:
    import pymupdf as fitz
except ImportError:
    import fitz


class PDFParser:
    """
    Extracts text content from PDF files using PyMuPDF (fitz).
    Handles text-based PDFs, multi-page documents, and cleans encoding artifacts.
    """

    def extract_text(self, file_path: str) -> list:
        """
        Extract all text from a PDF file, page by page.
        """
        pages = []
        try:
            document = fitz.open(file_path)
            for i, page in enumerate(document):
                raw_text = page.get_text() or ""
                # Replace common PDF encoding artifacts (e.g. replacement char \ufffd)
                cleaned_text = raw_text.replace("\ufffd", " ").replace("\x00", "")
                
                pages.append({
                    "text": cleaned_text,
                    "metadata": {
                        "page": i + 1,
                        "total_pages": len(document)
                    }
                })
            document.close()
        except Exception as e:
            print(f"[PDF PARSER ERROR] Failed to parse {file_path}: {e}")
            raise e

        return pages
