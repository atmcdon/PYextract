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
            full_text.append(page.get_text("text")) # "text" for plain text extraction
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

# --- How to use this PDF extraction and saving function ---

# Assume your previous section extraction function is defined elsewhere in your script
# (e.g., from your_section_parser_module import extract_sections_from_text, SectionData)
# Make sure the 'extract_sections_from_text' function and 'SectionData' Pydantic model
# from our previous discussion are available if you intend to use them later.

if __name__ == "__main__":
    pdf_path = "angi36-101.pdf"  # <--- CHANGE THIS TO YOUR PDF FILE'S PATH
    output_txt_path = "extracted_Text.txt" # Name of the output file

    print(f"Attempting to extract text from: {pdf_path}")
    extracted_pdf_text = extract_text_from_pdf(pdf_path)

    if extracted_pdf_text:
        print(f"Successfully extracted text from PDF. Total characters: {len(extracted_pdf_text)}")

        # Save the extracted text to extracted_Text.txt
        save_text_to_file(extracted_pdf_text, output_txt_path)

        # You can still print a sample if you like:
        print("\nFirst 500 characters of extracted text (also saved to file):\n")
        # print(extracted_pdf_text[:500] + "...")
        # print("-" * 50)

        # Now the 'extracted_pdf_text' variable holds the full text if you want to
        # pass it to your section extraction function, or you can read it from 'extracted_Text.txt'
        # in another step/script.
        # For example, to then process it for sections:
        #
        # sections = extract_sections_from_text(extracted_pdf_text) # Assuming this function is defined
        # if sections:
        #     # Process sections as before
        #     print(f"\nFound {len(sections)} sections in the extracted text.")
        # else:
        #     print("\nCould not extract structured sections from the PDF text.")

    else:
        print(f"Failed to extract text from {pdf_path}.")