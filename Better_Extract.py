import re
import pandas as pd
import time # Import time for progress updates
from docx import Document
from docx.document import Document as _Document
from docx.oxml.table import CT_Tbl
from docx.oxml.text.paragraph import CT_P
from docx.table import _Cell, Table
from docx.text.paragraph import Paragraph
import sys # To flush output
import traceback # For detailed error reporting
import os # Needed for path manipulation in saving partial results

# --- Configuration ---
DOC_PATH = "Copy of dafi36-2110.docx" # Ensure path is correct
OUTPUT_FILENAME = "will_references_formatted_output.csv" # New output filename
TARGET_WORD = "will" # The word to search for (case-insensitive)
PROGRESS_UPDATE_INTERVAL_SECONDS = 15 # How often to print progress
# Set to True to save partial results if errors occur during processing
SAVE_PARTIAL_RESULTS_ON_ERROR = True
# --- End Configuration ---


# Define the regex patterns
# Pattern to find the target word (whole word, case-insensitive)
target_word_pattern = re.compile(r"\b" + re.escape(TARGET_WORD) + r"\b", re.IGNORECASE)

# Pattern to identify section headings at the start of a paragraph
# Matches: A., B., 1., 1.2., 1.2.3, 1.2.3., etc., followed by optional space
section_pattern = re.compile(r"^(?:[A-Z]\.|\d+(\.\d+)*)\.?\s*")

def find_section_details(text):
    """
    Checks if text starts with a pattern defined by section_pattern.
    Returns the matched section identifier (e.g., "1.2.3.") and the rest of the text as the title.
    """
    match = section_pattern.match(text)
    if match:
        # match.group() gets the entire matched string (the section identifier)
        number = match.group().strip()
        # match.end() gives the index in the original string *after* the match
        title = text[match.end():].strip()
        return number, title
    return None, None

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
current_section_number = "N/A"
current_section_title = "N/A"
element_counter = 0 # Overall order of elements (paras/tables)
error_count = 0
last_print_time = start_time

# --- Optional Incremental Saving Setup (Keep commented unless needed) ---
# ... (incremental saving setup code omitted for brevity, remains commented) ...

print("Iterating through document body elements...")
sys.stdout.flush() # Ensure messages appear immediately

try: # Wrap the main iteration loop
    for block in iter_block_items(doc):
        element_counter += 1

        # Print progress periodically
        current_time = time.time()
        if current_time - last_print_time > PROGRESS_UPDATE_INTERVAL_SECONDS:
            elapsed_time = current_time - start_time
            rate = element_counter / elapsed_time if elapsed_time > 0 else 0
            print(f"  ... Processing element {element_counter}... "
                  f"Current section: '{current_section_number}'. "
                  f"Elapsed: {elapsed_time:.1f}s ({rate:.1f} elem/s). "
                  f"Found: {len(results)}. Errors: {error_count}")
            sys.stdout.flush()
            last_print_time = current_time

        try: # Add try-except around processing EACH block
            if isinstance(block, Paragraph):
                para_text = block.text.strip()
                if not para_text:
                    continue # Skip empty paragraphs

                # Check if this paragraph is a section heading
                sec_num, sec_title = find_section_details(para_text)
                if sec_num is not None:
                    # Update current section info
                    current_section_number = sec_num
                    # Use the rest of the para text as title, might be empty
                    current_section_title = sec_title if sec_title else "" # Ensure title is not None

                # Check for the target word in this paragraph
                matches = target_word_pattern.findall(para_text)
                if matches:
                    result_data = {
                        # Keep original keys matching data source
                        "Element Order": element_counter,
                        "Matches": len(matches),
                        "Section Number": current_section_number,
                        "Section Title": current_section_title,
                        "Text": para_text,
                        # Keep these internal if needed, but won't export by default
                        "Element Type": "Paragraph",
                        "Location Detail": f"Top-Level Paragraph"
                    }
                    results.append(result_data)
                    # --- Add Incremental Saving Logic here if using ---

            elif isinstance(block, Table):
                for i, row in enumerate(block.rows):
                    for j, cell in enumerate(row.cells):
                        cell_para_counter = 0
                        # Use iter_block_items recursively for cell content
                        for cell_block in iter_block_items(cell):
                             if isinstance(cell_block, Paragraph):
                                cell_para_counter += 1
                                cell_para_text = cell_block.text.strip()
                                if not cell_para_text:
                                    continue

                                # Check for target word in cell paragraph
                                matches = target_word_pattern.findall(cell_para_text)
                                if matches:
                                    result_data = {
                                        # Keep original keys matching data source
                                        "Element Order": element_counter, # Index of the parent Table element
                                        "Matches": len(matches),
                                        "Section Number": current_section_number,
                                        "Section Title": current_section_title,
                                        "Text": cell_para_text,
                                         # Keep these internal if needed, but won't export by default
                                        "Element Type": "Table Cell",
                                        "Location Detail": f"Table (Parent Elem {element_counter}), Row {i+1}, Col {j+1}, Cell Para {cell_para_counter}"
                                    }
                                    results.append(result_data)
                                    # --- Add Incremental Saving Logic here if using ---

        except Exception as block_processing_error:
            error_count += 1
            print(f"\n!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
            print(f"ERROR #{error_count} processing element {element_counter}!")
            print(f"Element Type encountered: {type(block)}")
            try:
                context_text = block.text[:200].strip() if hasattr(block, 'text') else "[Could not get text]"
                print(f"Context Text (up to 200 chars): '{context_text}'...")
            except Exception as text_err:
                print(f"[Could not retrieve text from problematic element: {text_err}]")
            print(f"Current Section when error occurred: {current_section_number} - {current_section_title}")
            print(f"Error Details: {block_processing_error}")
            # print("Traceback:")
            # traceback.print_exc() # Uncomment for full trace
            print(f"Attempting to continue processing next element...")
            print(f"!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n")
            sys.stdout.flush()
            continue # Continue to the next block item

except Exception as main_loop_error:
    # Catch errors happening *outside* the inner try-except (e.g., in iter_block_items)
    print(f"\n--- FATAL ERROR during main document iteration ---")
    print(f"Stopped near element number: {element_counter}")
    print(f"Current Section when error occurred: {current_section_number} - {current_section_title}")
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
        # Create a filename indicating partial results
        base, ext = os.path.splitext(OUTPUT_FILENAME)
        output_filename_to_use = f"{base}_PARTIAL_WITH_{error_count}_ERRORS{ext}"
        proceed_with_save = True
    else:
         print(f"⚠️ Processing encountered {error_count} errors. Final CSV not saved as SAVE_PARTIAL_RESULTS_ON_ERROR is False.")
         # results list remains, but proceed_with_save is False

    if proceed_with_save:
        try:
            df = pd.DataFrame(results)

            # --- Define and Select Columns for the desired format ---
            # Rename 'Element Order' -> 'Paragraph' for the output header to match the image
            df.rename(columns={"Element Order": "Paragraph"}, inplace=True)

            # Define the exact columns and order from the image
            desired_columns_order = [
                "Paragraph",      # Renamed from Element Order
                "Matches",
                "Section Number",
                "Section Title",
                "Text"
            ]

            # Ensure all desired columns exist in the DataFrame, adding empty ones if somehow missing
            for col in desired_columns_order:
                if col not in df.columns:
                    df[col] = "" # Add missing column with empty string

            # Select only the desired columns in the specified order
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


# --- Final Step for Incremental Saving (remains commented) ---
# ...

end_time = time.time()
total_time = end_time - start_time
print(f"\nTotal execution time: {total_time:.2f} seconds.")