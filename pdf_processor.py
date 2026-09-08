import io
import re

def extract_text_from_pdf(file_bytes_or_path):
    """
    Extracts text page by page from an uploaded PDF bytes or file path using pdfplumber.
    Returns:
        dict: {
            "raw_text": full combined text,
            "pages": [{"page_number": int, "text": str}],
            "page_count": int
        }
    """
    try:
        import pdfplumber
        pages_content = []
        combined_text = []

        if isinstance(file_bytes_or_path, (bytes, bytearray)):
            pdf_file = io.BytesIO(file_bytes_or_path)
        elif hasattr(file_bytes_or_path, 'read'):
            pdf_file = io.BytesIO(file_bytes_or_path.read())
        else:
            pdf_file = file_bytes_or_path

        with pdfplumber.open(pdf_file) as pdf:
            for idx, page in enumerate(pdf.pages, start=1):
                page_text = page.extract_text() or ""
                # Clean extra whitespaces
                cleaned_text = re.sub(r'[ \t]+', ' ', page_text).strip()
                if cleaned_text:
                    pages_content.append({"page_number": idx, "text": cleaned_text})
                    combined_text.append(cleaned_text)

        full_text = "\n\n".join(combined_text)
        return {
            "raw_text": full_text,
            "pages": pages_content,
            "page_count": len(pages_content) if pages_content else 1
        }
    except Exception as e:
        # Graceful fallback or error reporting
        return {
            "raw_text": f"Error reading PDF: {str(e)}",
            "pages": [],
            "page_count": 0,
            "error": str(e)
        }

def clean_extracted_text(text):
    """Clean redundant spaces and normalize newlines."""
    text = re.sub(r'\r\n', '\n', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()
