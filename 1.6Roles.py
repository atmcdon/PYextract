import re
import json

def extract_roles_and_responsibilities(input_file_path):
    """
    Extracts roles and responsibilities from a text file, focusing only on Chapter 2.

    Args:
        input_file_path (str): The path to the input text file.

    Returns:
        dict: A dictionary where keys are roles and values are their 
              corresponding responsibilities.
    """
    roles_dict = {}
    try:
        # Open the file with UTF-8 encoding to handle special characters
        with open(input_file_path, 'r', encoding='utf-8') as file:
            full_content = file.read()

        # 1. Isolate the content of Chapter 2 to prevent reading into other sections
        chapter_2_match = re.search(r"Chapter 2\s+ROLES AND RESPONSIBILITIES(.*?)(?=Chapter 3)", full_content, re.DOTALL)
        if not chapter_2_match:
            print("Error: Could not find the 'Chapter 2 ROLES AND RESPONSIBILITIES' section.")
            return None
        content = chapter_2_match.group(1)

        # 2. Split the chapter into sections based on the numbered headings.
        # This pattern splits the text but keeps the heading as a separate item in the list.
        sections = re.split(r'(\n2\.(?:\d\.)+.*)', content)
        
        # The resulting list is [intro_text, heading1, content1, heading2, content2, ...].
        # We iterate through this list, pairing each heading with its content.
        # We start from index 1 because index 0 is any text before the first heading.
        for i in range(1, len(sections), 2):
            role_title_raw = sections[i].strip()
            # Check if there is corresponding content for the heading
            if (i + 1) < len(sections):
                responsibility_raw = sections[i+1].strip()

                # Filter out section titles that are just containers for sub-roles
                # by checking if their content immediately starts with another section number.
                if responsibility_raw.startswith('2.'):
                    continue
                    
                # Clean the role title by removing the number prefix (e.g., "2.2.1.")
                role = re.sub(r'^2\.(?:\d\.)+\s*', '', role_title_raw).strip()
                if role.endswith('.'):
                    role = role[:-1]
                    
                # Clean up the responsibility text
                responsibility = responsibility_raw.replace('\n', ' ').strip()
                
                # Add the role and its responsibilities to the dictionary
                if role and responsibility:
                    roles_dict[role] = responsibility

    except FileNotFoundError:
        print(f"Error: The file at {input_file_path} was not found.")
        return None
    except UnicodeDecodeError as e:
        print(f"Error decoding file: {e}")
        print("Please ensure the input file is saved with UTF-8 encoding.")
        return None
        
    return roles_dict

def save_to_files(roles_dict, text_output_path, json_output_path):
    """
    Saves the roles and responsibilities to a text file and a JSON file.

    Args:
        roles_dict (dict): The dictionary of roles and responsibilities.
        text_output_path (str): The path to the output text file.
        json_output_path (str): The path to the output JSON file.
    """
    if roles_dict:
        # Save to a text file, ensuring UTF-8 encoding for output as well
        with open(text_output_path, 'w', encoding='utf-8') as file:
            for role, responsibility in roles_dict.items():
                file.write(f"Role: {role}\n")
                file.write(f"Responsibilities: {responsibility}\n\n")
        
        # Save to a JSON file for easy use in other programs
        with open(json_output_path, 'w', encoding='utf-8') as file:
            json.dump(roles_dict, file, indent=4, ensure_ascii=False)
            
        print(f"Successfully saved data to {text_output_path} and {json_output_path}")

# --- Main execution ---
if __name__ == "__main__":
    # Path to the input file containing the roles and responsibilities
    input_file = "reformatted_single_line_sections.txt"
    
       # Extract the data
    extracted_data = extract_roles_and_responsibilities(input_file)
    
    # Define the output file paths
    text_output_file = "extracted_roles.txt"
    json_output_file = "extracted_roles.json"
    
    # Save the data to the output files
    if extracted_data:
        save_to_files(extracted_data, text_output_file, json_output_file)
