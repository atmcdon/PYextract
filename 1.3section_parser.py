# section_parser.py
import re
import pandas as pd
from typing import List, Dict, Optional, Any

# --- Pydantic Model  ---
try:
    from pydantic import BaseModel
    class SectionData(BaseModel):
        section_number: str
        section_title: str
        content: str
        level: int
        parent_number: Optional[str] = None
        ancestry: List[str] = []
    USE_PYDANTIC = True
except ImportError:
    
    USE_PYDANTIC = False 
# --- End Pydantic Model ---

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

def get_hierarchy_info(section_number_str: str) -> Dict[str, Any]:
    
    #Derives level, parent_number, and ancestry from a section number string.
    
    parts = section_number_str.split('.')
    level = len(parts)
    parent_number = None
    ancestry = []

    if level > 1:
        parent_number = ".".join(parts[:-1])
        for i in range(1, level): # Create all ancestor strings
            ancestry.append(".".join(parts[:i]))
            
    return {
        "level": level,
        "parent_number": parent_number,
        "ancestry": ancestry
    }

def extract_sections_with_hierarchy(full_content_text: str) -> List[Any]: # Returns List of Pydantic objects or Dicts
    """
    Extracts ALL sections identified by numerical or A-prefixed numerical section numbers
    (e.g., 1., 1.2, A1.1.1), including their title, content, and hierarchical information.
    This parser expects content to potentially span multiple lines after the header line.
    """
    sections_found = []
    if not full_content_text:
        return sections_found

    cleaned_text = re.sub(r"--- PAGE \d+ ---\n?", "", full_content_text)
    # cleaned_text = re.sub(r"\\s?", "", cleaned_text) # If source markers are problematic

    # Refined Regex:
    # Looks for A?X. (e.g., 1., A1.) followed by optional .Y.Z.W patterns
    # This pattern requires the first numerical component to be followed by a dot.
    section_pattern = re.compile(
        r"^(?P<number>(?:A?\d{1,2}\.(?:\d{1,2}\.?)*))\s*(?P<title>.*?)$",
        re.MULTILINE
    )
    # Breakdown of number part: (?:A?\d{1,2}\.(?:\d{1,2}\.?)*)
    # A?             - Optional 'A'
    # \d{1,2}\.      - One or two digits FOLLOWED BY A LITERAL DOT (e.g., "1.", "12.", "A1.").
    # (?:\d{1,2}\.?)* - Optionally, more groups of (one/two digits and an optional trailing dot for that subgroup).
    #                  This allows matching "1.1", "1.1.2", "1.1.2." etc.

    matches = list(section_pattern.finditer(cleaned_text))

    if not matches:
        print("No section headers found with the defined pattern (e.g., 1., 2.1., A1.1).")
        return []

    for i, current_match in enumerate(matches):
        # Strip trailing dots from the captured section number for cleaner output
        section_number_raw = current_match.group("number").strip().rstrip('.')
        section_title_raw = current_match.group("title").strip() # Title is the rest of the header line
        
        hierarchy_info = get_hierarchy_info(section_number_raw)
        
        content_start_index = current_match.end() # Content starts *after* the header line
        content_end_index = len(cleaned_text)
        if i + 1 < len(matches):
            content_end_index = matches[i+1].start() # Content ends at start of *next* header
        
        content_raw = cleaned_text[content_start_index:content_end_index].strip()

        current_section_data = {
            "section_number": section_number_raw,
            "section_title": section_title_raw,
            "content": content_raw,
            "level": hierarchy_info["level"],
            "parent_number": hierarchy_info["parent_number"],
            "ancestry": hierarchy_info["ancestry"]
        }

        if USE_PYDANTIC:
            try:
                sections_found.append(SectionData(**current_section_data))
            except Exception as e: # Pydantic ValidationError
                 print(f"Pydantic validation error for section '{section_number_raw}': {e} - storing as dict.")
                 sections_found.append(current_section_data) # Fallback to dict
        else:
            sections_found.append(current_section_data)
            
    return sections_found

# Main execution block to read a text file, extract sections, and save to CSV
# This is designed to process all sections found by the regex in the input text file.
if __name__ == "__main__":
    # This script will now process ALL sections found by the regex
    input_text_path = "reformatted_single_line_sections.txt"  # <--- INPUT: Text file 
    output_csv_path = "all_sections_with_hierarchy.csv" # Output CSV for all sections

    print(f"Attempting to read and parse all sections from: {input_text_path}")
    document_text = read_text_from_file(input_text_path)

    if document_text:
        all_extracted_data = extract_sections_with_hierarchy(document_text)

        if all_extracted_data:
            print(f"\nExtracted {len(all_extracted_data)} sections with hierarchy:\n")
            # Example: Print info for the first few sections
            for section_info_item in all_extracted_data[:5]: # Print first 5 as a sample
                num = section_info_item.section_number if USE_PYDANTIC else section_info_item['section_number']
                title = section_info_item.section_title if USE_PYDANTIC else section_info_item['section_title']
                lvl = section_info_item.level if USE_PYDANTIC else section_info_item['level']
                parent = section_info_item.parent_number if USE_PYDANTIC else section_info_item['parent_number']
                
                print(f"  Number: {num}, Level: {lvl}, Parent: {parent}")
                print(f"  Title: {title[:70]}...") # Truncate title for display
                print("-" * 40)
            
            # Saving all extracted sections to a CSV file
            if USE_PYDANTIC:
                # Filter out any non-Pydantic objects if a mix occurred due to validation errors
                pydantic_objects = [s for s in all_extracted_data if isinstance(s, SectionData)]
                data_for_df = [section.model_dump() for section in pydantic_objects]
                if len(data_for_df) < len(all_extracted_data): # If there were fallbacks to dict
                    print("Warning: Some sections had Pydantic validation errors and were processed as dictionaries.")
                    data_for_df = [] # Rebuild ensuring all are dicts
                    for item in all_extracted_data:
                        if isinstance(item, SectionData): data_for_df.append(item.model_dump())
                        else: data_for_df.append(item)
            else:
                data_for_df = all_extracted_data
            
            if data_for_df:
                try:
                    df = pd.DataFrame(data_for_df)
                    column_order = ["section_number", "level", "parent_number", "ancestry", "section_title", "content"]
                    for col in column_order: # Ensure all desired columns are present
                        if col not in df.columns:
                            df[col] = None
                    df = df[column_order] # Order them
                    df.to_csv(output_csv_path, index=False, encoding='utf-8')
                    print(f"\nAll extracted section data saved to {output_csv_path}")
                except Exception as e:
                    print(f"\nCould not save to CSV: {e}. Ensure pandas is installed (pip install pandas).")
            else:
                print("\nNo valid data to save to CSV (possibly all Pydantic validations failed or no sections extracted).")
        else:
            print(f"No sections were extracted from '{input_text_path}'.")
    else:
        print(f"Could not read the document from '{input_text_path}'.")