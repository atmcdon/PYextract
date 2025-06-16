# text_reformatter.py
import re
from typing import Optional

def read_text_from_file(filepath: str) -> Optional[str]:
    """Reads content from a text file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as file:
            content = file.read()
        return content
    except FileNotFoundError:
        print(f"Error: File not found at {filepath}")
        return None
    except Exception as e:
        print(f"Error reading file: {e}")
        return None

def reformat_raw_text_to_single_line_sections(raw_text: str) -> str:
    
    if not raw_text:
        return ""

    # This regex identifies the start of each section line (header).
    # It should match the numerical patterns you're interested in (e.g., 1.2.3. or A1.1.1.).
    # This pattern looks for at least two numerical components (e.g., X.Y).
    section_header_pattern = re.compile(
        r"^(?:A\d{1,2}(?:\.\d{1,2}){1,3}\.?|\d{1,2}(?:\.\d{1,2}){1,3}\.?)\s*.*$",
        re.MULTILINE
    )
    
    reformatted_output_lines = []
    matches = list(section_header_pattern.finditer(raw_text))
    
    if not matches:
        # If no specific section markers are found, make the entire text a single line.
        print("No section markers found for reformatting; entire text will be one line.")
        return raw_text.replace('\n', ' ').strip()

    last_block_end = 0
    # Handle text before the first match (if any)
    if matches[0].start() > 0:
        pre_section_text = raw_text[0:matches[0].start()]
        cleaned_pre_section_text = pre_section_text.replace('\n', ' ').strip()
        if cleaned_pre_section_text:
             reformatted_output_lines.append(cleaned_pre_section_text)
    
    for i, match in enumerate(matches):
        current_block_start = match.start() # Start of the current section's header line
        
        current_block_end = len(raw_text)
        if i + 1 < len(matches):
            current_block_end = matches[i+1].start() # End is start of next section's header line
            

        # This block includes the header and all content lines of the current section
        # Extract the text for the current section
        section_text_block = raw_text[current_block_start:current_block_end]
        single_line_section = section_text_block.replace('\n', ' ').strip() # Replace newlines within block
        
        if single_line_section:
            reformatted_output_lines.append(single_line_section)
            
    return "\n".join(reformatted_output_lines) # Each "section" is now a single line, separated by newlines.

def save_text_to_file(text_content: str, output_filepath: str) -> None:
    """Saves the given text content to a specified file."""
    try:
        with open(output_filepath, 'w', encoding='utf-8') as file:
            file.write(text_content)
        print(f"Successfully saved reformatted text to: {output_filepath}")
    except Exception as e:
        print(f"Error saving text to file: {e}")




if __name__ == "__main__":

    
    input_raw_text_path = "raw_extracted_text.txt"  # <--- INPUT: 
    output_reformatted_path = "reformatted_single_line_sections.txt"

    print(f"Attempting to read raw text from: {input_raw_text_path}")
    raw_text = read_text_from_file(input_raw_text_path)

    if raw_text:
        print("Reformatting text...")
        reformatted_content = reformat_raw_text_to_single_line_sections(raw_text)
        save_text_to_file(reformatted_content, output_reformatted_path)
        # print(f"\nSample of reformatted text:\n{reformatted_content[:500]}...")
    else:
        print(f"Failed to read raw text from {input_raw_text_path}.")