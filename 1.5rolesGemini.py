import json
import google.generativeai as genai
import os

# --- Configuration ---
try:
    genai.configure(api_key=os.environ["GEMINI_API_KEY"])
except KeyError:
    print("Error: GEMINI_API_KEY environment variable not set.")
    print("Please set the GEMINI_API_KEY environment variable or replace 'os.environ[\"GEMINI_API_KEY\"]' with your actual key.")
    exit()

# Initialize the Gemini model
model = genai.GenerativeModel('gemini-pro')

def load_roles_data(file_path):
    """Loads the roles data from a JSON file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: Roles data file not found at {file_path}")
        return []
    except json.JSONDecodeError as e:
        print(f"Error decoding roles data JSON: {e}")
        return []

def load_system_prompt_template(file_path):
    """Loads the system prompt template from a text file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        print(f"Error: System prompt file not found at {file_path}")
        return ""

def format_roles_for_prompt(roles_list):
    """Formats the list of roles into a readable string for the prompt."""
    formatted_roles = []
    for role in roles_list:
        name = role.get("name", "N/A")
        abbreviation = role.get("abbreviation", "")
        if abbreviation:
            formatted_roles.append(f"- {name} ({abbreviation})")
        else:
            formatted_roles.append(f"- {name}")
    return "\n".join(formatted_roles)

def extract_role_string_with_gemini(text_chunk_json_str, system_prompt_template, roles_data):
    """
    Uses the Gemini API to extract *only* the 'role' string from a given text chunk JSON.

    Args:
        text_chunk_json_str (str): The full JSON string content of the chunk.
        system_prompt_template (str): The loaded template for the system prompt.
        roles_data (list): The list of dictionaries containing role names and abbreviations.

    Returns:
        str: The extracted role string, or "Role not found" if not identified or an error occurs.
    """
    formatted_roles_list = format_roles_for_prompt(roles_data)
    
    # Replace the placeholder in the system prompt template
    full_prompt_instructions = system_prompt_template.replace("<ROLES_LIST>", formatted_roles_list)

    # For gemini-pro, system instructions are part of the user prompt
    prompt = f"{full_prompt_instructions}\n{text_chunk_json_str}"
    
    try:
        response = model.generate_content(prompt)
        # Gemini's response should now be just the role string
        return response.text.strip()
    except Exception as e:
        print(f"Error calling Gemini API: {e}")
        return "Role not found" # Default if API call fails

def process_file_and_extract_roles(input_file_path, output_file_path, system_prompt_path, roles_data_path):
    """
    Reads the input file, extracts JSON chunks, finds roles using Gemini,
    updates the 'role' field, and writes to an output file.

    Args:
        input_file_path (str): The path to the input file.
        output_file_path (str): The path to the output file where updated JSONs will be saved.
        system_prompt_path (str): Path to the system prompt text file.
        roles_data_path (str): Path to the roles data JSON file.
    """
    updated_chunks = []
    current_chunk_str = ""
    brace_count = 0
    in_chunk = False

    # Load roles data and system prompt template once
    roles_data = load_roles_data(roles_data_path)
    system_prompt_template = load_system_prompt_template(system_prompt_path)

    if not roles_data or not system_prompt_template:
        print("Failed to load necessary data (roles or system prompt). Exiting.")
        return

    try:
        with open(input_file_path, 'r', encoding='utf-8') as infile:
            for line in infile:
                stripped_line = line.strip()

                if stripped_line == "{":
                    in_chunk = True
                    brace_count += 1
                    current_chunk_str += stripped_line + "\n"
                elif in_chunk:
                    current_chunk_str += stripped_line + "\n"
                    if stripped_line == "}":
                        brace_count -= 1
                        if brace_count == 0:
                            # End of a chunk
                            try:
                                chunk_data = json.loads(current_chunk_str)
                                
                                # Check if the 'role' field is empty
                                if not chunk_data.get("role"):
                                    # Extract role string using Gemini
                                    identified_role = extract_role_string_with_gemini(current_chunk_str, system_prompt_template, roles_data)
                                    
                                    # Update the 'role' field in the dictionary
                                    # Ensure "Role not found" is literally stored if that's the outcome
                                    chunk_data["role"] = identified_role
                                else:
                                    # If role is already present, keep it as is
                                    print(f"Chunk ID: {chunk_data.get('id', 'N/A')} already has a role. Skipping API call.")

                                updated_chunks.append(chunk_data)

                            except json.JSONDecodeError as e:
                                print(f"Error decoding JSON chunk: {e}\nChunk content:\n{current_chunk_str}")
                            except Exception as e:
                                print(f"An unexpected error occurred while processing chunk: {e}\nChunk content:\n{current_chunk_str}")
                            finally:
                                current_chunk_str = ""
                                in_chunk = False
                                brace_count = 0
                    else:
                        brace_count += stripped_line.count('{')
                        brace_count -= stripped_line.count('}')

    except FileNotFoundError:
        print(f"Error: Input file not found at {input_file_path}")
        return
    except Exception as e:
        print(f"An error occurred during file processing: {e}")
        return
    
    # Write updated chunks to the output file
    try:
        with open(output_file_path, 'w', encoding='utf-8') as outfile:
            # Write each JSON object on a new line, or format as a JSON array
            # For simplicity, let's write them as separate JSON objects, one per line
            # If you want a single JSON array, you'd wrap them in [ ] and add commas
            for chunk in updated_chunks:
                outfile.write(json.dumps(chunk, indent=4) + "\n") # Using indent=4 for pretty-printing
        print(f"\nProcessing complete. Updated data saved to '{output_file_path}'")
    except Exception as e:
        print(f"Error writing to output file: {e}")

# --- Main execution ---
if __name__ == "__main__":
    input_file_path = 'parsed_document_chunks.txt' # Your input data file
    output_file_path = 'updated_parsed_document_chunks.txt' # Output file for updated data
    roles_data_path = 'roles_data.json' # The new roles data file
    system_prompt_path = 'system_prompt.txt' # The new system prompt file

    # --- Create dummy files for demonstration if they don't exist ---
    if not os.path.exists(roles_data_path):
        print(f"Creating a dummy roles data file '{roles_data_path}' for demonstration.")
        dummy_roles_content = """
[
  {
    "name": "Assistant Secretary of the Air Force for Manpower and Reserve Affairs",
    "abbreviation": "SAF/MR"
  },
  {
    "name": "Deputy Chief of Staff for Manpower, Personnel and Services",
    "abbreviation": "AF/A1"
  },
  {
    "name": "Headquarters Air Force Reserve Command, Chief, Military Personnel Division",
    "abbreviation": "AFRC, A1K"
  },
  {
    "name": "Installation/Wing/Delta/Group/Unit Commanders",
    "abbreviation": ""
  },
  {
    "name": "Director, Manpower, Personnel, Recruiting, and Services",
    "abbreviation": "NGB/A1"
  }
]
        """
        with open(roles_data_path, 'w', encoding='utf-8') as f:
            f.write(dummy_roles_content.strip())

    if not os.path.exists(system_prompt_path):
        print(f"Creating a dummy system prompt file '{system_prompt_path}' for demonstration.")
        dummy_prompt_content = """
You are an expert in military organizational structures, especially those within the US Air Force and Space Force. Your task is to identify specific organizational roles from provided JSON text.

Here is a list of known military roles and their abbreviations for reference:
<ROLES_LIST>

Given the "text" field from the JSON input, identify and extract the most accurate organizational role.
If the "role" key in the original JSON is empty, you must fill it based on the content of the "text" field.
You should try to match the identified role to one of the "name" values in the provided list. If you find a direct match, output the "name" as is. If you find a close match, prioritize the name from the list. If the role is not explicitly in the list but clearly identifiable from the text, provide the role as it appears in the text. If you find an abbreviation in the text, try to match it to a known abbreviation and provide the corresponding full "name" from the list.

If no specific role can be identified or inferred from the "text" field, output "Role not found".
Your output should ONLY be the identified role string, or "Role not found". Do not output the entire JSON again.

Input JSON:
        """
        with open(system_prompt_path, 'w', encoding='utf-8') as f:
            f.write(dummy_prompt_content.strip())

    if not os.path.exists(input_file_path):
        print(f"Creating a dummy input file '{input_file_path}' for demonstration.")
        dummy_input_content = """
{
"id": "chunk_230",
"role": "Source: reformatted_single_line_sections.txt",
"header": "2.3.1.1",
"text": "Serve as decision authority for all AFR assignment requests that are not addressed within this instruction.",
"preceding_header_ids": ["2.3.1"],
"preceding_chunk_ids": ["chunk_226", "chunk_227"]
}
{
"id": "chunk_231",
"role": "",
"header": "2.3.2",
"text": "Headquarters Air Force Reserve Command (AFRC), Chief, Military Personnel Division (AIK) is the OPR for Assignment of Personnel Assigned to AFR and will:",
"preceding_chunk_ids": ["chunk_226"]
}
{
"id": "chunk_232",
"role": "Source: reformatted_single_line_sections.txt",
"header": "2.3.3",
"text": "Interpret AF/AFR policy as it relates to AFR personnel.",
"preceding_header_ids": ["2.3.2"],
"preceding_chunk_ids": ["chunk_226", "chunk_231"]
}
{
"id": "chunk_233",
"role": "",
"header": "2.3.9.2",
"text": "Provide guidance and documentation instructions to the MPF for unit program.",
"preceding_chunk_ids": ["chunk_231"]
}
{
"id": "chunk_234",
"role": "",
"header": "2.3.9.3",
"text": "I am an Installation/Wing/Delta/Group/Unit Commander.",
"preceding_chunk_ids": ["chunk_231"]
}
{
"id": "chunk_235",
"role": "",
"header": "2.3.9.4",
"text": "This policy is issued by NGB/A1 for all personnel.",
"preceding_chunk_ids": ["chunk_231"]
}
"""
        with open(input_file_path, 'w', encoding='utf-8') as f:
            f.write(dummy_input_content.strip())
        print("Dummy input file created. You can replace its content with your actual data.")
    # --- End dummy file creation ---

    # Run the processing
    process_file_and_extract_roles(input_file_path, output_file_path, system_prompt_path, roles_data_path)

    # Optional: Read and print the updated output file to verify
    print(f"\n--- Content of '{output_file_path}' ---")
    try:
        with open(output_file_path, 'r', encoding='utf-8') as f:
            print(f.read())
    except FileNotFoundError:
        print("Output file not found.")