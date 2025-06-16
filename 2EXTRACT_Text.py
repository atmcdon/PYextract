import re
import fitz  # PyMuPDF
from typing import Optional, List

# Function to extract all text from PDF (remains the same)
def extract_text_from_pdf(pdf_filepath: str) -> Optional[str]:
    """
    Extracts all text content from a PDF file.
    """
    try:
        doc = fitz.open(pdf_filepath)
        full_text = []
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            full_text.append(page.get_text("text"))
        doc.close()
        return "\n".join(full_text)
    except FileNotFoundError:
        print(f"Error: PDF file not found at {pdf_filepath}")
        return None
    except Exception as e:
        print(f"Error extracting text from PDF: {e}")
        return None

# This is the function that reformats the text as you want for extracted_Text.txt
def reformat_raw_text_to_single_line_sections(raw_text: str) -> str:
    
    if not raw_text:
        return ""

    # This regex identifies the start of each section line (header).
    # It should match the numerical patterns you're interested in,
    # e.g., "1.2.3." or "A1.1.1."
    section_header_pattern = re.compile(
        r"^(?:A\d{1,2}(?:\.\d{1,2}){1,3}\.?|\d{1,2}(?:\.\d{1,2}){1,3}\.?)\s*.*$",
        re.MULTILINE
    )
    
    reformatted_output_lines = []
    matches = list(section_header_pattern.finditer(raw_text))
    
    if not matches:
        # If no specific section markers are found, treat the whole text as one block
        # and convert all its newlines to spaces.
        return raw_text.replace('\n', ' ').strip()

    last_block_end = 0
    # Handle any text that might appear before the first recognized section header
    if matches[0].start() > 0:
        pre_section_text = raw_text[0:matches[0].start()]
        cleaned_pre_section_text = pre_section_text.replace('\n', ' ').strip()
        if cleaned_pre_section_text: # Add only if it's not just whitespace
             reformatted_output_lines.append(cleaned_pre_section_text)
    
    for i, match in enumerate(matches):
        current_block_start = match.start() # Start of the current section's header line
        
        current_block_end = len(raw_text)
        if i + 1 < len(matches):
            current_block_end = matches[i+1].start() # End is start of next section's header line
            
        # This block includes the header and all content lines of the current section
        section_text_block = raw_text[current_block_start:current_block_end]
        
        # Replace all newlines within this block with a single space, then strip
        single_line_section = section_text_block.replace('\n', ' ').strip()
        
        if single_line_section: # Avoid adding empty lines
            reformatted_output_lines.append(single_line_section)
            
    return "\n".join(reformatted_output_lines) # Each reformatted section on a new line in the output string


def save_text_to_file(text_content: str, output_filepath: str) -> None:
    """
    Saves the given text content to a specified file.
    """
    try:
        with open(output_filepath, 'w', encoding='utf-8') as file:
            file.write(text_content)
        print(f"Successfully saved text to: {output_filepath}")
    except Exception as e:
        print(f"Error saving text to file: {e}")

# --- Main execution block ---
if __name__ == "__main__":
    pdf_path = "Copy of dafi36-2110-1.pdf"  # <--- YOUR PDF FILE
    output_txt_path = "extracted_Text.txt" # Output file with single-line sections

    print(f"Attempting to extract raw text from: {pdf_path}")
    raw_extracted_pdf_text = extract_text_from_pdf(pdf_path)

    if raw_extracted_pdf_text:
        print(f"Successfully extracted raw text from PDF.")

        print("\nReformatting text so each section (header + content) is a single line...")
        reformatted_text = reformat_raw_text_to_single_line_sections(raw_extracted_pdf_text)
        
        save_text_to_file(reformatted_text, output_txt_path)
        
        # If you want to see a sample of what's saved to extracted_Text.txt:
        # print("\nSample of reformatted text (first few hundred characters):")
        print(reformatted_text[:500] + "...")

        # NOTE: If you then use the other script ('extract_sections_from_text' which
        # identifies number, title, and multi-line content) on THIS 'extracted_Text.txt'
        # file, it will behave differently because each section is now one long line.
        # That parser would likely see the section number correctly, but the entire
        # rest of the long line might become the 'section_title', with 'content' being empty.
        # This reformatted file is specifically for the "single line per section" output you requested.
    else:
        print(f"Failed to extract text from {pdf_path}.")