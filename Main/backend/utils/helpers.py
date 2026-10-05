import json
import os
import re


def safe_json_parse(text: str) -> dict:
    """
    Safely parse JSON from LLM responses.
    Handles common issues like markdown code fences and trailing commas.
    Returns an empty dict on failure instead of raising.
    """

    # Strip markdown code fences
    cleaned = text.strip()
    cleaned = cleaned.replace("```json", "")
    cleaned = cleaned.replace("```", "")
    cleaned = cleaned.strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    # Try to extract JSON object from surrounding text
    match = re.search(r'\{.*\}', cleaned, re.DOTALL)

    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    return {}


def clean_text(text: str) -> str:
    """
    Clean and normalize extracted document text.
    Removes excessive whitespace, replacement characters, page markers, and common OCR artifacts.
    """
    if not text:
        return ""

    # Strip replacement characters and null bytes
    text = text.replace('\ufffd', ' ').replace('\x00', '')

    # Collapse multiple newlines into double newlines
    text = re.sub(r'\n{3,}', '\n\n', text)

    # Collapse multiple spaces into single space
    text = re.sub(r' {2,}', ' ', text)

    # Remove common page markers
    text = re.sub(
        r'Page\s+\d+\s*(of\s+\d+)?',
        '',
        text,
        flags=re.IGNORECASE
    )

    # Strip leading/trailing whitespace from each line
    lines = text.split('\n')
    lines = [line.strip() for line in lines]
    text = '\n'.join(lines)

    return text.strip()


def get_file_extension(file_path: str) -> str:
    """
    Extract and normalize the file extension from a path.
    Returns lowercase extension without the dot (e.g., 'pdf', 'docx').
    """

    _, ext = os.path.splitext(file_path)

    return ext.lower().lstrip('.')


def detect_file_type(file_path: str) -> str:
    """
    Classify a file into a document type based on its extension.
    Returns one of: 'pdf', 'docx', 'excel', 'image', 'unknown'.
    """

    ext = get_file_extension(file_path)

    pdf_types = {'pdf'}
    docx_types = {'docx', 'doc'}
    excel_types = {'xlsx', 'xls', 'csv'}
    image_types = {'png', 'jpg', 'jpeg', 'bmp', 'tiff', 'tif'}

    if ext in pdf_types:
        return 'pdf'

    if ext in docx_types:
        return 'docx'

    if ext in excel_types:
        return 'excel'

    if ext in image_types:
        return 'image'

    return 'unknown'
