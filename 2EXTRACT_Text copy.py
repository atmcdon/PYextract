import re
import pandas as pd
from typing import List, Optional

# --- Pydantic Model (Optional) ---
try:
    from pydantic import BaseModel
    class SectionData(BaseModel):
        section_number: str
        # section_title: str # Title can be made optional or removed
        section_title: Optional[str] = None # Making title optional
        content: str
    USE_PYDANTIC = True
except ImportError:
    print("Pydantic library not found. Output will be dictionaries.")
    USE_PYDANTIC = False
# --- End Pydantic Model ---

def read_text_from_file(filepath: str) -> Optional[str]:
    """Reads content from a text file."""
    # ... (same as before) ...
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

def extract_sections_from_text_content_starts_on_header_line(full_content_text: str) -> List:
    """
    Extracts sections. The 'content' starts on the same line as the section number,
    after the number itself. The 'title' will be empty or very minimal.
    """
    sections = []
    if not full_content_text:
        return sections

    cleaned_text = re.sub(r"--- PAGE \d+ ---\n?", "", full_content_text)

    # Regex to capture number. The rest of the line will be part of the content.
    # We capture the number, and then separately the rest of the line.
    section_header_line_pattern = re.compile(
        r"^(?P<number>(?:A\d{1,2}(?:\.\d{1,2}){1,3}\.?|\d{1,2}(?:\.\d{1,2}){1,3}\.?))(?P<first_line_of_content>.*?)$",
        re.MULTILINE
    )

    matches = list(section_header_line_pattern.finditer(cleaned_text))

    if not matches:
        print("No section headers matching the refined numerical pattern found.")
        return []

    for i, current_match in enumerate(matches):
        section_number_raw = current_match.group("number").strip().rstrip('.')
        # The rest of the header line is now considered the beginning of the content
        first_line_content = current_match.group("first_line_of_content").strip()

        # Determine where the full content block for this section ends
        content_block_end_index = len(cleaned_text)
        if i + 1 < len(matches):
            content_block_end_index = matches[i+1].start()

        # The full content starts from the beginning of 'first_line_content' within the header match
        # and goes up to the start of the next section.
        # We need to reconstruct the content from current_match.start('first_line_of_content')
        # relative to cleaned_text.

        # The content for this section starts from where the title *would have* started
        # on the header line.
        content_start_for_this_section = current_match.start('first_line_of_content')
        full_content_for_section = cleaned_text[content_start_for_this_section:content_block_end_index].strip()
        
        # In this model, the title is effectively empty or just the number itself if you prefer
        # For clarity, let's keep title as minimal or empty.
        section_title_raw = "" # Or you could extract a very short phrase if identifiable

        if USE_PYDANTIC:
            try:
                section_obj = SectionData(
                    section_number=section_number_raw,
                    section_title=section_title_raw, # Explicitly empty or minimal
                    content=full_content_for_section
                )
                sections.append(section_obj)
            except Exception as e:
                print(f"Pydantic validation error for section '{section_number_raw}': {e}")
                sections.append({
                    "section_number": section_number_raw,
                    "section_title": section_title_raw,
                    "content": full_content_for_section
                })
        else:
            sections.append({
                "section_number": section_number_raw,
                "section_title": section_title_raw, # Explicitly empty or minimal
                "content": full_content_for_section
            })
    return sections

# --- How to use the script ---
if __name__ == "__main__":
    file_path = "extracted_Text.txt"
    document_text = read_text_from_file(file_path)

    if document_text:
        # Using the original function first to demonstrate its behavior:
        print("--- Using Original Logic (Title is the first line after number) ---")
        # To use the original extract_sections_from_text, ensure it's defined
        # For this example, I'll assume your last posted script's version:
        # extracted_data_original = extract_sections_from_text(document_text)
        # if extracted_data_original:
        #     for section_info in extracted_data_original[:2]: # Show first 2 for brevity
        #         print(f"Section Number: {section_info['section_number']}")
        #         print(f"Section Title: {section_info['section_title']}")
        #         print(f"Content (first 100 chars): {section_info['content'][:100]}...")
        #         print("-" * 40)

        print("\n\n--- Using New Logic (Content starts on header line, minimal/no title) ---")
        extracted_data_new_logic = extract_sections_from_text_content_starts_on_header_line(document_text)

        if extracted_data_new_logic:
            for section_info in extracted_data_new_logic: # Show first few for brevity
                if USE_PYDANTIC and isinstance(section_info, SectionData):
                    print(f"Section Number: {section_info.section_number}")
                    if section_info.section_title: # Print title only if it's not empty
                         print(f"Section Title: {section_info.section_title}")
                    print(f"Content (first 100 chars): {section_info.content[:100]}...")
                else:
                    print(f"Section Number: {section_info['section_number']}")
                    if section_info['section_title']:
                        print(f"Section Title: {section_info['section_title']}")
                    print(f"Content (first 100 chars): {section_info['content'][:100]}...")
                print("-" * 40)

            # Saving to CSV (using the new logic's output)
            if USE_PYDANTIC:
                data_for_df = [s.model_dump() for s in extracted_data_new_logic if isinstance(s, SectionData)]
            else:
                data_for_df = extracted_data_new_logic
            
            if data_for_df:
                try:
                    df = pd.DataFrame(data_for_df)
                    df.to_csv("extracted_sections_content_on_header.csv", index=False, encoding='utf-8')
                    print(f"\nData from new logic saved to extracted_sections_content_on_header.csv")
                except Exception as e:
                    print(f"\nCould not save new logic data to CSV: {e}.")
        else:
            print(f"No sections were extracted with the new logic from '{file_path}'.")
    else:
        print(f"Could not read the document from '{file_path}'.")