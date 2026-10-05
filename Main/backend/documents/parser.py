import fitz  # PyMuPDF


class PDFParser:
    """
    Handles PDF parsing and text extraction.
    """

    def extract_text(self, file_path: str) -> str:
        """
        Extract all text from a PDF file.
        """

        document = fitz.open(file_path)

        text = ""

        for page in document:
            text += page.get_text()

        document.close()

        return text