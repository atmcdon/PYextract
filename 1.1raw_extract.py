# pdf_extractor.py
import fitz  # PyMuPDF
from typing import Optional

def extract_text_from_pdf(pdf_filepath: str) -> Optional[str]:
    """
    Extracts all text content from a PDF file.
    Args:
        pdf_filepath (str): The path to the PDF file.
    Returns:
        str: The extracted text content from all pages, or None if an error occurs.
    """
    try:
        doc = fitz.open(pdf_filepath)
        full_text = []
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            full_text.append(page.get_text("text"))  # "text" for plain text extraction
        doc.close()
        return "\n".join(full_text)
    except FileNotFoundError:
        print(f"Error: PDF file not found at {pdf_filepath}")
        return None
    except Exception as e:
        print(f"Error extracting text from PDF: {e}")
        return None

def save_text_to_file(text_content: str, output_filepath: str) -> None:
    """
    Saves the given text content to a specified file.
    Args:
        text_content (str): The text content to save.
        output_filepath (str): The path to the output text file.
    """
    try:
        with open(output_filepath, 'w', encoding='utf-8') as file:
            file.write(text_content)
        print(f"Successfully saved extracted text to: {output_filepath}")
    except Exception as e:
        print(f"Error saving text to file: {e}")

if __name__ == "__main__":
    input_pdf_path = "Copy of dafi36-2110-1.pdf"  # <---  INPUT
    output_raw_text_path = "raw_extracted_text.txt"

    print(f"Attempting to extract text from: {input_pdf_path}")
    extracted_pdf_text = extract_text_from_pdf(input_pdf_path)

    if extracted_pdf_text:
        print(f"Successfully extracted text from PDF. Total characters: {len(extracted_pdf_text)}")
        save_text_to_file(extracted_pdf_text, output_raw_text_path)
    else:
        print(f"Failed to extract text from {input_pdf_path}.")