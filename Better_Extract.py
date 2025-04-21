import re
import pandas as pd
import time
from docx import Document
from docx.document import Document as _Document
from docx.oxml.table import CT_Tbl
from docx.oxml.text.paragraph import CT_P
from docx.table import _Cell, Table
from docx.text.paragraph import Paragraph
import sys
import traceback
import os

# --- Configuration ---
DOC_PATH = "Copy of dafi36-2110.docx"
OUTPUT_FILENAME = "will_references_formatted_output_v2.csv" # Updated filename
TARGET_WORD = "will"
PROGRESS_UPDATE_INTERVAL_SECONDS = 15
SAVE_PARTIAL_RESULTS_ON_ERROR = True
# Set the specific element number or a unique text snippet to trigger debug prints
DEBUG_ELEMENT_NUMBER = 401 # Adjust if needed based on previous runs
DEBUG_TEXT_SNIPPET = "Assignment of family members" # Adjust if needed

# --- Constants for Section Flagging ---
NO_SECTION_FLAG_INTERNAL = None
NO_SECTION_FLAG_OUTPUT = "no section numbering"
# --- End Configuration ---


# Define the regex patterns
target_word_pattern = re.compile(r"\b" + re.escape(TARGET_WORD) + r"\b", re.IGNORECASE)

section_pattern = re.compile(r"^\s*(?:[A-Z]\.|\d+(\.\d+)*\.)\s*")
def find_section_details(text):
    """
    Checks if text starts with a section pattern. Returns number and title.
    The returned 'number' should be the clearly defined section identifier.
    """
    match = section_pattern.match(text)
    if match:
        number = match.group().strip() # Captures the full matched prefix (e.g., "1.2.3." or "A.")
        title = text[match.end():].strip()
        return number, title
    return None, None # Return None if the pattern doesn't match

def iter_block_items(parent):
    """
    Yields each paragraph and table child within *parent*, in document order.
    Handles basic error checking for unexpected element types during iteration.
    """
    if isinstance(parent, _Document):
        parent_elm = parent.element.body
    elif isinstance(parent, _Cell):
        parent_elm = parent._tc
    else:
        # print(f"Warning: Unsupported parent type for iteration: {type(parent)}")
        return # Gracefully handle unsupported types

    if parent_elm is None: # Added check for None parent element
         # print(f"Warning: Parent element is None for parent type {type(parent)}")
         return

    for child in parent_elm.iterchildren():
        try:
            if isinstance(child, CT_P):
                yield Paragraph(child, parent)
            elif isinstance(child, CT_Tbl):
                yield Table(child, parent)
            # Add other block-level element types here if needed (e.g., CT_SdtBlock)
        except Exception as e:
            # This might catch issues during Paragraph/Table object instantiation
            print(f"\n--- Error instantiating Paragraph/Table object from child element ---")
            print(f"Child Element Tag: {child.tag}")
            print(f"Parent Type: {type(parent)}")
            print(f"Error: {e}")
            # traceback.print_exc() # Uncomment for full traceback here
            print(f"Attempting to skip this problematic element...")
            continue # Skip this child and try the next

# --- Main Processing ---
start_time = time.time()
print(f"Starting document processing for '{TARGET_WORD}'...")
print(f"Loading document: {DOC_PATH}")
sys.stdout.flush()

try:
    doc = Document(DOC_PATH)
    print(f"Document '{DOC_PATH}' loaded successfully.")
except Exception as e:
    print(f"FATAL ERROR: Could not load document: {e}")
    traceback.print_exc()
    exit()

results = []
# Initialize current_section_number with the internal flag (None)
current_section_number = NO_SECTION_FLAG_INTERNAL
current_section_title = "" # Title starts empty
element_counter = 0
error_count = 0
last_print_time = start_time

print("Iterating through document body elements...")
sys.stdout.flush()

try: # Wrap the main iteration loop
    for block in iter_block_items(doc):
        element_counter += 1

        # --- Check if this element should trigger Debugging ---
        # Set flag to True if conditions are met, simplifies following checks
        is_debug_target = False
        temp_para_text_for_debug_check = "" # Avoid getting text multiple times if not needed
        if isinstance(block, Paragraph):
            temp_para_text_for_debug_check = block.text.strip()
            if element_counter == DEBUG_ELEMENT_NUMBER or (DEBUG_TEXT_SNIPPET and DEBUG_TEXT_SNIPPET in temp_para_text_for_debug_check):
                 is_debug_target = True
        # --- End Debug Trigger Check ---

        # Print progress periodically
        current_time = time.time()
        if current_time - last_print_time > PROGRESS_UPDATE_INTERVAL_SECONDS:
            elapsed_time = current_time - start_time
            rate = element_counter / elapsed_time if elapsed_time > 0 else 0
            # Display current section number; handle None case for printing
            section_display = current_section_number if current_section_number is not None else "[No Section Yet]"
            print(f"  ... Processing element {element_counter}... "
                  f"Current section: '{section_display}'. "
                  f"Elapsed: {elapsed_time:.1f}s ({rate:.1f} elem/s). "
                  f"Found: {len(results)}. Errors: {error_count}")
            sys.stdout.flush()
            last_print_time = current_time

        try: # Add try-except around processing EACH block
            if isinstance(block, Paragraph):
                # Use the text we might have already retrieved for the debug check
                para_text = temp_para_text_for_debug_check if is_debug_target else block.text.strip()

                if not para_text:
                    continue # Skip empty paragraphs

                # --- >>> DEBUG PRINT 1 <<< ---
                if is_debug_target:
                   print(f"\nDEBUG ---- Element {element_counter} ----")
                   print(f"DEBUG Text Start: '{para_text[:150]}...'")
                   print(f"DEBUG Current Section BEFORE Check: '{current_section_number}'")

                # Check if this paragraph IS a section heading
                sec_num, sec_title = find_section_details(para_text)
                if sec_num is not None:
                     # --- >>> DEBUG PRINT 2 <<< ---
                    if is_debug_target:
                        print(f"DEBUG Section DETECTED in this para: Num='{sec_num}', Title='{sec_title[:50]}...'")
                    # Update current section info. sec_num is the clearly defined number.
                    current_section_number = sec_num
                    current_section_title = sec_title if sec_title else "" # Ensure title is not None
                # --- >>> DEBUG PRINT 2.5 (Else case) <<< ---
                elif is_debug_target: # Only print else case if it's the target paragraph
                     print(f"DEBUG Section NOT detected at the start of this para.")


                # Check for the target word ("will") in this paragraph's text
                matches = target_word_pattern.findall(para_text)
                if matches:
                    # --- >>> DEBUG PRINT 3 <<< ---
                    if is_debug_target:
                        print(f"DEBUG '{TARGET_WORD}' FOUND in this para.")
                        print(f"DEBUG Recording Section Number: '{current_section_number}'") # Check this value carefully!
                        print(f"DEBUG Recording Section Title: '{current_section_title}'")

                    # Append result, using the current section number (which might be None or updated)
                    result_data = {
                        "Element Order": element_counter,
                        "Matches": len(matches),
                        "Section Number": current_section_number, # Store the actual number OR the None flag
                        "Section Title": current_section_title if current_section_number is not None else "", # Only store title if section exists
                        "Text": para_text,
                        "Element Type": "Paragraph", # Internal use
                        "Location Detail": f"Top-Level Paragraph" # Internal use
                    }
                    results.append(result_data)

                    if is_debug_target:
                       print(f"DEBUG Result Appended.")
                       print(f"--------------------------\n")


            elif isinstance(block, Table):
                # Process table cells, associating with the current section number
                # (No debug prints added inside table processing for now)
                for i, row in enumerate(block.rows):
                    for j, cell in enumerate(row.cells):
                        cell_para_counter = 0
                        for cell_block in iter_block_items(cell):
                             if isinstance(cell_block, Paragraph):
                                cell_para_counter += 1
                                cell_para_text = cell_block.text.strip()
                                if not cell_para_text:
                                    continue

                                matches = target_word_pattern.findall(cell_para_text)
                                if matches:
                                    # Append result, using the current section number (which might be None)
                                    result_data = {
                                        "Element Order": element_counter,
                                        "Matches": len(matches),
                                        "Section Number": current_section_number, # Store the actual number OR the None flag
                                        "Section Title": current_section_title if current_section_number is not None else "", # Only store title if section exists
                                        "Text": cell_para_text,
                                        "Element Type": "Table Cell", # Internal use
                                        "Location Detail": f"Table (Parent Elem {element_counter}), Row {i+1}, Col {j+1}, Cell Para {cell_para_counter}" # Internal use
                                    }
                                    results.append(result_data)

        except Exception as block_processing_error:
            # ... (error handling for block processing remains the same) ...
            error_count += 1
            print(f"\n!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
            print(f"ERROR #{error_count} processing element {element_counter}!")
            print(f"Element Type encountered: {type(block)}")
            try:
                context_text = block.text[:200].strip() if hasattr(block, 'text') else "[Could not get text]"
                print(f"Context Text (up to 200 chars): '{context_text}'...")
            except Exception as text_err:
                print(f"[Could not retrieve text from problematic element: {text_err}]")
            section_display_err = current_section_number if current_section_number is not None else "[No Section Yet]"
            print(f"Current Section when error occurred: {section_display_err} - {current_section_title}")
            print(f"Error Details: {block_processing_error}")
            print(f"Attempting to continue processing next element...")
            print(f"!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n")
            sys.stdout.flush()
            continue

except Exception as main_loop_error:
    # ... (error handling for main loop remains the same) ...
    print(f"\n--- FATAL ERROR during main document iteration ---")
    print(f"Stopped near element number: {element_counter}")
    section_display_fatal = current_section_number if current_section_number is not None else "[No Section Yet]"
    print(f"Current Section when error occurred: {section_display_fatal} - {current_section_title}")
    print(f"Error: {main_loop_error}")
    print("Traceback:")
    traceback.print_exc()
    sys.stdout.flush()

# --- Final Saving Step ---
print("\nProcessing finished or stopped due to error.")
print(f"Total elements processed (or attempted): {element_counter}")
print(f"Total '{TARGET_WORD}' instances found: {len(results)}")
print(f"Total errors encountered while processing elements: {error_count}")

final_save_attempted = False
output_filename_to_use = OUTPUT_FILENAME # Default filename

if results:
    # Decide whether to save based on errors and config
    proceed_with_save = False
    if error_count == 0:
        print("Saving results to CSV...")
        proceed_with_save = True
        output_filename_to_use = OUTPUT_FILENAME
    elif SAVE_PARTIAL_RESULTS_ON_ERROR:
        print(f"⚠️ Saving partial results as {error_count} errors were encountered during processing.")
        base, ext = os.path.splitext(OUTPUT_FILENAME)
        output_filename_to_use = f"{base}_PARTIAL_WITH_{error_count}_ERRORS{ext}"
        proceed_with_save = True
    else:
         print(f"⚠️ Processing encountered {error_count} errors. Final CSV not saved as SAVE_PARTIAL_RESULTS_ON_ERROR is False.")

    if proceed_with_save:
        try:
            df = pd.DataFrame(results)

            # --- Apply Section Number Flagging for Output ---
            # Replace the internal flag (None) with the desired output string
            df['Section Number'] = df['Section Number'].fillna(NO_SECTION_FLAG_OUTPUT)
            # Also ensure Section Title is blank if Section Number was flagged
            df.loc[df['Section Number'] == NO_SECTION_FLAG_OUTPUT, 'Section Title'] = ""
            # --- End Section Number Flagging ---


            # --- Define and Select Columns for the desired format ---
            df.rename(columns={"Element Order": "Paragraph"}, inplace=True)
            desired_columns_order = [
                "Paragraph",
                "Matches",
                "Section Number", # Now contains the flag string where appropriate
                "Section Title",
                "Text"
            ]
            for col in desired_columns_order:
                if col not in df.columns:
                    df[col] = "" # Add missing column
            df_final = df[desired_columns_order]
            # ---------------------------------------------------------

            df_final.to_csv(output_filename_to_use, index=False, encoding='utf-8-sig')
            print(f"✅ Done! Saved {len(df_final)} instances to '{output_filename_to_use}'")
            final_save_attempted = True
        except Exception as e:
            print(f"ERROR saving final CSV file ('{output_filename_to_use}'): {e}")
            traceback.print_exc()

elif error_count > 0:
     print(f"ℹ️ No '{TARGET_WORD}' instances found, and {error_count} errors occurred during processing. No CSV file created.")
else:
    print(f"ℹ️ No instances of '{TARGET_WORD}' found in the document. No CSV file created.")
# --- End Final Saving ---

end_time = time.time()
total_time = end_time - start_time
print(f"\nTotal execution time: {total_time:.2f} seconds.")