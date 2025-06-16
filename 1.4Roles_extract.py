import re

def find_and_extract_roles_section(text):
    """
    Dynamically finds the 'Roles and Responsibilities' chapter from the TOC,
    then extracts the content of that entire chapter for parsing.

    Args:
        text (str): The full text of the policy document.

    Returns:
        str or None: The text of the relevant chapter, or None if not found.
    """

    # # containing "roles and responsibilities", and captures the main chapter number.
    # toc_pattern = re.compile(r"^\s*(?P<chapter>\d+)[.\d]*\s*.*?roles\s+and\s+responsibilities", re.MULTILINE | re.IGNORECASE)
    # toc_match = toc_pattern.search(text)

    # if not toc_match:
    #     print("Could not find 'Roles and Responsibilities' in the Table of Contents.")
    #     return None

    # chapter_number = int(toc_match.group('chapter'))
    # next_chapter_number = chapter_number + 1
    # print(f"Found 'Roles and Responsibilities' in Chapter {chapter_number}. Setting extraction boundaries...")

  
    # This pattern flexibly finds "Chapter X" with spaces, dashes, or newlines.
    # start_marker = re.compile(fr"(?i)Chapter[\s—-]+{chapter_number}")
    # end_marker = re.compile(fr"(?i)Chapter[\s—-]+{next_chapter_number}")

    start_marker = re.compile(fr"(?i)Chapter[\s—-]+1")
    end_marker = re.compile(fr"(?i)Chapter[\s—-]+4")

    # 3. Find the start and end positions of the chapter content
    start_match = start_marker.search(text)
    if not start_match:
        print(f"Error: Found Chapter 1 in TOC, but could not find the chapter heading in the document body.")
        return None

    # Search for the end marker *after* the start marker
    end_match = end_marker.search(text, pos=start_match.end())

    if not end_match:
        
        chapter_text = text[start_match.start():]
    else:
        
        chapter_text = text[start_match.start():end_match.start()]

    return chapter_text




import re

def parse_roles_from_text(section_text):
    

    role_pattern = re.compile(
        r'([A-Za-z\s.,-]+?)\s+\(([A-Za-z0-9/-]+)\)', 
        re.MULTILINE | re.IGNORECASE
    )
    
    found_roles = role_pattern.findall(section_text)

    print(f"Found {found_roles} roles and abbreviations in the section text.")

    roles_dict = {}
    for role, abbr in found_roles:
        # Clean the role by stripping whitespace and removing extra spaces
        clean_role = ' '.join(role.strip().split())
        
        # Standardize the abbreviation to uppercase
        roles_dict[clean_role] = abbr.upper()
            
    return roles_dict









def save_roles_to_txt(roles_dict, output_filename):
    """Saves the dictionary of roles and abbreviations to a text file."""
    try:
        with open(output_filename, 'w', encoding='utf-8') as file:
            for role, abbreviation in roles_dict.items():
                file.write(f"Role: {role}\n")
                file.write(f"abbreviation: ({abbreviation})\n\n")
        return f"Successfully exported the roles to '{output_filename}'"
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

    # Step 1: Dynamically find and extract the correct chapter's content
    roles_chapter_text = find_and_extract_roles_section(full_text)

    if not roles_chapter_text:
        print("Processing stopped because the relevant section could not be found.")
        return

    # Step 2: Parse the roles from the extracted chapter text
    extracted_roles = parse_roles_from_text(roles_chapter_text)

    if not extracted_roles:
        print("No roles and abbreviations were found within the identified chapter.")
        return

    # Step 3: Save the results to a file
    result_message = save_roles_to_txt(extracted_roles, output_filename)
    print(result_message)


# --- How to Use ---
# 1. Save your full policy document into a file (e.g., 'policy_document.txt').
# 2. Set the filenames below and run the script.
input_file = 'reformatted_single_line_sections.txt'  # This should be the file containing the full policy document
output_file = 'parsed_roles_and_responsibilities.txt'

process_policy_document(input_file, output_file)