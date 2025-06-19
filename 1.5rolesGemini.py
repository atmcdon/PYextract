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
model = genai.GenerativeModel('gemini-2.0-flash')


#load_roles_data(file_path):
def load_roles_data(file_path):
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: Roles data file not found at {file_path}")
        return []
    except json.JSONDecodeError as e:
        print(f"Error decoding roles data JSON: {e}")
        return []

# Loads the system prompt template from a text file.
def load_system_prompt_template(file_path):
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        print(f"Error: System prompt file not found at {file_path}")
        return ""

# Formats the list of roles into a readable string for the prompt.
def format_roles_for_prompt(roles_list):
    
    formatted_roles = []
    for role in roles_list:
        name = role.get("name")
        abbreviation = role.get("abbreviation", "")
        if abbreviation:
            formatted_roles.append(f"- {name} ({abbreviation})")
        else:
            formatted_roles.append(f"- {name}")
    return "\n".join(formatted_roles)






# # Uses the Gemini API to extract the 'role' string from a given text chunk JSON.
def extract_role_string_with_gemini(text_chunk_json_str, system_prompt_template, roles_data):
    
    # Uses the Gemini API to extract *only* the 'role' string from a given text chunk JSON.

    # Args:
        # text_chunk_json_str (str): The full JSON string content of the chunk.
        # system_prompt_template (str): The loaded template for the system prompt.
        # roles_data (list): The list of dictionaries containing role names and abbreviations.

    # Returns:
        # str: The extracted role string, or "Role not found" if not identified or an error occurs.
    
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


                if not stripped_line or stripped_line.startswith("---"):
                    if in_chunk:
                        # If we were in a chunk and hit an empty line or separator, finalize the current chunk
                        print(f"STRIPED LINe: {stripped_line}")
                        current_chunk_str = ""  # Reset current chunk string
                        in_chunk = False
                        brace_count = 0
                    continue


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
            
            for chunk in updated_chunks:
                outfile.write(json.dumps(chunk, indent=4) + "\n") 
        print(f"\nProcessing complete. Updated data saved to '{output_file_path}'")
    except Exception as e:
        print(f"Error writing to output file: {e}")




# --- Main execution ---
if __name__ == "__main__":
   

    input_file_path = 'parsed_document_chunks copy.txt' 
    output_file_path = 'updated_parsed_document_chunks.txt' 
    roles_data_path = 'roles.json' 
    system_prompt_path = 'system_prompt.txt' 



    # dummy data creation for demonstration purposes
    # Check if the input file exists, if not, create a dummy file for demonstration
    if not os.path.exists(input_file_path):
        print(f"Creating a dummy file '{input_file_path}' for demonstration.")
        dummy_content = """
{
    "id": "chunk_088",
    "role": "",
    "header": "3.1.2.3.1.",
    "text": "In partnership with the AETC/TPM, identify issues; establish the agenda;  determine participants, time frame, location, and additional staffing requirements;  ensure minutes are prepared and distributed; and monitor the status of action items. The  CFM and AETC/TPM signs and publishes the minutes before adjourning the STRT  and U&TW. Note: If the STRT was held without a U&TW, only the CFM signs the  meeting minutes.",
    "preceding_header_ids": ["3.1.", "3.1.2.", "3.1.2.3."],
    "preceding_chunk_ids": ["chunk_082", "chunk_084", "chunk_087"]
}
{
    "id": "chunk_089",
    "role": "",
    "header": "3.1.2.3.2.",
    "text": "Chair the portion of the STRT and U&TW for utilization, authorization, and  general career field mission issues.",
    "preceding_header_ids": ["3.1.", "3.1.2.", "3.1.2.3."],
    "preceding_chunk_ids": ["chunk_082", "chunk_084", "chunk_087"]
}
{
    "id": "chunk_090",
    "role": "",
    "header": "3.1.2.3.3.",
    "text": "Ensure direct involvement and participation of subject-matter experts from  the field.",
    "preceding_header_ids": ["3.1.", "3.1.2.", "3.1.2.3."],
    "preceding_chunk_ids": ["chunk_082", "chunk_084", "chunk_087"]
}
{
    "id": "chunk_091",
    "role": "",
    "header": "3.1.2.3.4.",
    "text": "Ensure, where applicable, the direct involvement and participation of the AF  Career Development Academy (AFCDA) personnel in STRT/U&TW proceedings  impacting development, revision, or deletion of CDCs or specialized courses used for  career field upgrade training.",
    "preceding_header_ids": ["3.1.", "3.1.2.", "3.1.2.3."],
    "preceding_chunk_ids": ["chunk_082", "chunk_084", "chunk_087"]
}
{
    "id": "chunk_092",
    "role": "",
    "header": "3.1.2.3.5.",
    "text": "Develop a CFETP for life-cycle training at appropriate points throughout a  career path.",
    "preceding_header_ids": ["3.1.", "3.1.2.", "3.1.2.3."],
    "preceding_chunk_ids": ["chunk_082", "chunk_084", "chunk_087"]
}
{
    "id": "chunk_093",
    "role": "",
    "header": "3.1.2.3.5.1.",
    "text": "Ensure conformity with formatting, standardization, and publication  guidance along with currency and accuracy of technical references cited in the  CFETP.",
    "preceding_header_ids": ["3.1.", "3.1.2.", "3.1.2.3.", "3.1.2.3.5."],
    "preceding_chunk_ids": ["chunk_082", "chunk_084", "chunk_087", "chunk_092"]
}
{
    "id": "chunk_094",
    "role": "",
    "header": "3.1.2.3.5.2.",
    "text": "Ensure risk management processes are incorporated in all applicable areas  of training in concert with the U&TW process. It is the CFM\u2019s responsibility to specify  the exact risk management-related tasks and identify offsets or additional resources for  this training.   10  DAFMAN36-2689  31 MARCH 2023",
    "preceding_header_ids": ["3.1.", "3.1.2.", "3.1.2.3.", "3.1.2.3.5."],
    "preceding_chunk_ids": ["chunk_082", "chunk_084", "chunk_087", "chunk_092"]
}
{
    "id": "chunk_095",
    "role": "",
    "header": "3.1.2.3.5.3.",
    "text": "Establish the career field progression within the CFETP. AF CFMs  must ensure their respective CFETP embodies Airmanship and incorporates the  following competencies that align with the Air Force foundational competencies:  communication, accountability, teamwork, analytical thinking, and resource  management.  (T-1) This foundational competency requirement should be  accomplished through attrition and during respective STRTs with support from Air  Education and Training Command, Occupational Competencies Branch  (AETC/A3J), SF CFMs must ensure their respective CFETP embodies the  Guardian Ideal with support from Space Delta 13 (STARCOM).",
    "preceding_header_ids": ["3.1.", "3.1.2.", "3.1.2.3.", "3.1.2.3.5."],
    "preceding_chunk_ids": ["chunk_082", "chunk_084", "chunk_087", "chunk_092"]
}
{
    "id": "chunk_096",
    "role": "",
    "header": "3.1.2.3.5.4.",
    "text": "Validate training requirements in coordination with the MFMs and  NGB CFMs and identify training detachment-provided training in CFETP.",
    "preceding_header_ids": ["3.1.", "3.1.2.", "3.1.2.3.", "3.1.2.3.5."],
    "preceding_chunk_ids": ["chunk_082", "chunk_084", "chunk_087", "chunk_092"]
}
{
    "id": "chunk_097",
    "role": "",
    "header": "3.1.2.3.5.5.",
    "text": "Ensure final version of the CFETP is coordinated with AFPC/DP3D  and AETC/TPM using DAF Form 673, Department of the Air Force  Publication/Form Action Request, prior to publication through AF Departmental  Publishing Office.",
    "preceding_header_ids": ["3.1.", "3.1.2.", "3.1.2.3.", "3.1.2.3.5."],
    "preceding_chunk_ids": ["chunk_082", "chunk_084", "chunk_087", "chunk_092"]
}
"""
        with open(input_file_path, 'w') as f:
            f.write(dummy_content.strip())
        print("Dummy file created. You can replace its content with your actual data.")


   # Run the processing
    process_file_and_extract_roles(input_file_path, output_file_path, system_prompt_path, roles_data_path)

    
    print(f"\n--- Content of '{output_file_path}' ---")
    try:
        with open(output_file_path, 'r', encoding='utf-8') as f:
            print(f.read())
    except FileNotFoundError:
        print("Output file not found.")
