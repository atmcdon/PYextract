import re
import json # Used for cleanly formatting the list of preceding headers

def parse_document_into_chunks(text):
    """
    Parses a full document text into a list of structured "chunks" based on
    numbered section headers.

    Args:
        text (str): The full text of the policy document.

    Returns:
        list: A list of dictionaries, where each dictionary represents a chunk.
    """
    print("Parsing document into structured chunks...")
    
    
    header_pattern = re.compile(r"^\s*(\d+(\.\d+)*\.)\s+", re.MULTILINE)

    
    parts = header_pattern.split(text)

    
    if parts and parts[0].strip() == "":
        parts = parts[1:]

    chunks = []
    header_stack = [] #  hierarchy, e.g., ['2.', '2.2.', '2.2.3.']
    
    
    for i in range(0, len(parts), 2):
        if i + 1 >= len(parts):
            continue

        header = parts[i].strip()
        content = parts[i+1].strip()

        
        current_depth = header.count('.')
        
        
        while header_stack and header_stack[-1].count('.') >= current_depth:
            header_stack.pop()

        preceding_headers = list(header_stack) # Copy the stack for the record

        header_stack.append(header)
        

        chunk_data = {
            "id": f"chunk_{len(chunks) + 1:03d}", # e.g., chunk_001, chunk_002
            "header": header,
            "text": content,
            "preceding_header_ids": preceding_headers
        }
        chunks.append(chunk_data)

    print(f"Successfully parsed {len(chunks)} chunks.")
    return chunks


def save_chunks_to_txt(chunks, output_filename, source_filename=""):
    """
    Saves the list of structured chunks to a human-readable text file.

    Args:
        chunks (list): The list of chunk dictionaries.
        output_filename (str): The path to the output text file.
        source_filename (str): The name of the source file to reference in the output.
    """
    print(f"Saving chunks to '{output_filename}'...")
    try:
        with open(output_filename, 'w', encoding='utf-8') as file:
            for i, chunk in enumerate(chunks):
                file.write("{\n")
                file.write(f'    "id": "{chunk["id"]}",\n')
                # The 'role' field from your diagram seems to represent the source.
                # We use the source filename here for context.
                file.write(f'    "role": "Source: {source_filename}",\n')
                file.write(f'    "header": "{chunk["header"]}",\n')
                
                # Use json.dumps to ensure the text is a valid JSON string literal
                # This handles newlines and quotes correctly.
                formatted_text = json.dumps(chunk["text"])
                file.write(f'    "text": {formatted_text},\n')
                
                # Format the list of preceding headers
                preceding_list_str = json.dumps(chunk["preceding_header_ids"])
                file.write(f'    "preceding_header_ids": {preceding_list_str}\n')
                file.write("}\n")
                
                # Add a separator between chunks, unless it's the last one
                if i < len(chunks) - 1:
                    file.write("\n---\n\n")

        return f"Successfully exported the chunks to '{output_filename}'"
    except IOError as e:
        return f"Error: Could not write to file. Reason: {e}"


# --- Main Execution ---
def process_policy_document(input_filename, output_filename):
    """Main function to orchestrate the document processing."""
    try:
        with open(input_filename, 'r', encoding='utf-8') as file:
            full_text = file.read()
    except FileNotFoundError:
        print(f"Error: The input file '{input_filename}' was not found.")
        return

    # Step 1: Parse the document into structured chunks
    extracted_chunks = parse_document_into_chunks(full_text)

    if not extracted_chunks:
        print("No chunks were parsed from the document.")
        return

    # Step 2: Save the results to a file
    result_message = save_chunks_to_txt(extracted_chunks, output_filename, source_filename=input_filename)
    print(result_message)


# --- How to Use ---
# 1. Save your full policy document into a file (e.g., 'policy_document.txt').
# 2. Set the filenames below and run the script.
input_file = 'reformatted_single_line_sections.txt'
output_file = 'parsed_document_chunks.txt'

process_policy_document(input_file, output_file)