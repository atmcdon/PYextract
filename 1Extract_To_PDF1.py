import re
import fitz  # PyMuPDF
from typing import Optional, List

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

def reformat_raw_text_to_single_line_sections(raw_text: str) -> str:
    """
    Reformats raw extracted text so that each logical section (header + content)
    becomes a single line by replacing internal newlines with spaces.
    Sections are delimited by lines starting with patterns like X.Y.Z or AX.Y.Z.
    """
    if not raw_text:
        return ""

    # This regex identifies the start of each section line (header).
    # It's the same pattern used by your section parser for robust identification.
    section_header_pattern = re.compile(
        r"^(?:A\d{1,2}(?:\.\d{1,2}){1,3}\.?|\d{1,2}(?:\.\d{1,2}){1,3}\.?)\s*.*$",
        re.MULTILINE
    )
    
    reformatted_output_lines = []
    last_split_point = 0
    
    matches = list(section_header_pattern.finditer(raw_text))
    
    if not matches:
        # If no section markers are found, treat the whole text as one block
        # or return it as is, or process it line by line if desired.
        # For "append text till it finds the next...", if none found, implies one block.
        return raw_text.replace('\n', ' ').strip()

    for i, match in enumerate(matches):
        # Determine the start of the current section's block
        # This includes the header line itself
        current_block_start = match.start()
        
        # Text before the very first recognized section header
        if i == 0 and current_block_start > 0:
            pre_section_text = raw_text[0:current_block_start]
            # Decide how to handle pre-section text. For now, let's also make it a single line.
            # Or you could choose to prepend it to the first section, or save it separately.
            reformatted_output_lines.append(pre_section_text.replace('\n', ' ').strip())

        # Determine the end of the current section's block
        current_block_end = len(raw_text)
        if i + 1 < len(matches):
            current_block_end = matches[i+1].start()
            
        # Get the full text for the current section (header + its content)
        section_text_block = raw_text[current_block_start:current_block_end]
        
        # Replace all internal newlines in this block with a space, then strip
        single_line_section = section_text_block.replace('\n', ' ').strip()
        
        if single_line_section: # Avoid empty lines if a block was just whitespace
            reformatted_output_lines.append(single_line_section)
            
    return "\n".join(reformatted_output_lines)


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
        print(f"Successfully saved text to: {output_filepath}")
    except Exception as e:
        print(f"Error saving text to file: {e}")

# --- How to use the script ---

if __name__ == "__main__":
    pdf_path = "angi36-101.pdf"  # <--- CHANGE THIS TO YOUR PDF FILE'S PATH
    output_txt_path = "extracted_Text.txt" # Name of the output file

    print(f"Attempting to extract raw text from: {pdf_path}")
    raw_extracted_pdf_text = extract_text_from_pdf(pdf_path)

    if raw_extracted_pdf_text:
        print(f"Successfully extracted raw text from PDF. Total characters: {len(raw_extracted_pdf_text)}")

        # Reformat the raw text into single lines per section
        print("\nReformatting text for single-line sections...")
        reformatted_text_for_file = reformat_raw_text_to_single_line_sections(raw_extracted_pdf_text)
        
        # Save the REFORMATTED text to extracted_Text.txt
        save_text_to_file(reformatted_text_for_file, output_txt_path)
        
        # If you want to see a sample of the reformatted text:
        # print("\nFirst 500 characters of reformatted text (saved to file):\n")
        # print(reformatted_text_for_file[:500] + "...")
        # print("-" * 50)

        # IMPORTANT NOTE:
        # The 'reformatted_text_for_file' now has each section as a single long line.
        # If you intend to use your *original* 'extract_sections_from_text' parser
        # (which expects titles on one line and content on potentially multiple subsequent lines)
        # on THIS reformatted text, it might not work as expected.
        # That parser would need to be adapted to handle input where entire sections are on single lines.
        #
        # If you still need the structured (number, title, multi-line content) output
        # for the CSV, you should run the original section parser on the 'raw_extracted_pdf_text'.
        #
        # Example (if you have the original parser defined as extract_sections_from_text_original):
        #
        # from your_original_parser import extract_sections_from_text as extract_sections_from_text_original
        # structured_sections = extract_sections_from_text_original(raw_extracted_pdf_text)
        # if structured_sections:
        #     # Save structured_sections to CSV as before
        #     print(f"\nFound {len(structured_sections)} sections for structured output.")
        # else:
        #     print("\nCould not extract structured sections from the raw PDF text.")

    else:
        print(f"Failed to extract text from {pdf_path}.")