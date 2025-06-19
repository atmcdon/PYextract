import json
import google.generativeai as genai
import os
from dotenv import load_dotenv # NEW: Import load_dotenv

# --- Configuration ---
# NEW: Load environment variables from .env file
load_dotenv() 

try:
    # UPDATED: Access the API key from environment variables (now loaded from .env)
    genai.configure(api_key=os.environ["GEMINI_API_KEY"]) 
except KeyError:
    print("Error: GEMINI_API_KEY not found. Please ensure it's set in your .env file or as an environment variable.")
    exit()

# Initialize the Gemini model
# CHANGED: Model name to 'gemini-1.5-flash' for wider availability and good context window.
# If you explicitly have access to 'gemini-2.0-flash', keep it as is.
model = genai.GenerativeModel('gemini-1.5-flash')


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
        name = role.get("name")
        abbreviation = role.get("abbreviation", "")
        if name: # Ensure name exists
            if abbreviation:
                formatted_roles.append(f"- {name} ({abbreviation})")
            else:
                formatted_roles.append(f"- {name}")
    return "\n".join(formatted_roles)


# CHANGED: Function signature to accept temperature_value
def extract_role_string_with_gemini(full_context_prompt_text, roles_data, temperature_value): 
    """
    Uses the Gemini API to extract *only* the 'role' string from a given text chunk JSON,
    incorporating external system prompt, roles data, and contextual information.

    Args:
        full_context_prompt_text (str): The complete prompt text including system instructions, roles data,
                                         and the current chunk plus its surrounding context.
        roles_data (list): The list of dictionaries containing role names and abbreviations. (Used by format_roles_for_prompt)
        temperature_value (float): The temperature setting for the model.

    Returns:
        str: The extracted role string, or "Role not found" if not identified or an error occurs.
    """
    
    # NEW: Create a GenerationConfig object
    generation_config = genai.GenerationConfig(
        temperature=temperature_value,
        # You can add other parameters here if needed, e.g., top_p, top_k, max_output_tokens
        # top_p=0.95, 
        # top_k=60,   
        # max_output_tokens=100 
    )

    try:
        # CHANGED: Pass generation_config to generate_content
        response = model.generate_content(
            contents=[
                {"role": "user", "parts": [{"text": full_context_prompt_text}]}
            ],
            generation_config=generation_config
        )
        return response.text.strip()
    except Exception as e:
        print(f"Error calling Gemini API: {e}")
        return "Role not found" # Default if API call fails


# CHANGED: Added model_temperature parameter
def process_file_and_extract_roles(input_file_path, output_file_path, system_prompt_path, roles_data_path, model_temperature):
    """
    Reads the input file, extracts JSON chunks, finds roles using Gemini,
    updates the 'role' field, and writes to an output file.

    Args:
        input_file_path (str): The path to the input file.
        output_file_path (str): The path to the output file where updated JSONs will be saved.
        system_prompt_path (str): Path to the system prompt text file.
        roles_data_path (str): Path to the roles data JSON file.
        model_temperature (float): The temperature setting for the Gemini model.
    """
    all_chunks_raw_str = [] # NEW: Store all raw chunk strings for context
    updated_chunks = []
    
    # Load roles data and system prompt template once
    roles_data = load_roles_data(roles_data_path)
    system_prompt_template = load_system_prompt_template(system_prompt_path)
    formatted_roles_list = format_roles_for_prompt(roles_data) # NEW: Format roles once
    
    if not roles_data or not system_prompt_template:
        print("Failed to load necessary data (roles or system prompt). Exiting.")
        return

    # First pass: Read all chunks and store them. This is necessary to get preceding/succeeding context.
    current_chunk_str_builder = [] # Use a list for efficient string building
    brace_count = 0
    in_chunk = False
    try:
        with open(input_file_path, 'r', encoding='utf-8') as infile:
            for line_num, line in enumerate(infile, 1): # NEW: track line_num for better error messages
                stripped_line = line.strip()

                if not stripped_line or stripped_line.startswith("---"):
                    if in_chunk: # If we were in a chunk and hit an empty line or separator, finalize the current chunk
                        # This means a malformed chunk or unexpected separator inside
                        print(f"Warning: At file line {line_num}: Encountered separator or empty line '{stripped_line}' inside a JSON chunk. Skipping this potentially corrupted chunk.")
                        current_chunk_str_builder = []  # Reset current chunk string
                        in_chunk = False
                        brace_count = 0
                    continue # Skip this line

                # If we encounter a '{' at the start of a line and not currently in a chunk, it's a new chunk
                if stripped_line == "{":
                    if in_chunk: # If we see '{' but already in a chunk, previous chunk was malformed
                         print(f"Warning: At file line {line_num}: Encountered new chunk start '{{' before previous chunk completed. Skipping previous malformed chunk.")
                         current_chunk_str_builder = []
                         brace_count = 0 # Reset brace count for the new chunk
                    
                    in_chunk = True
                    brace_count += 1
                    current_chunk_str_builder.append(stripped_line)
                elif in_chunk:
                    current_chunk_str_builder.append(stripped_line)
                    if stripped_line == "}":
                        brace_count -= 1
                        if brace_count == 0:
                            # End of a chunk detected
                            full_chunk_str = "\n".join(current_chunk_str_builder)
                            all_chunks_raw_str.append(full_chunk_str) # Store raw string for later
                            current_chunk_str_builder = [] # Reset for next chunk
                            in_chunk = False
                            
                    else: # Ensure we count braces for lines that are not '{' or '}' but are part of the chunk
                        brace_count += stripped_line.count('{')
                        brace_count -= stripped_line.count('}')

    except FileNotFoundError:
        print(f"Error: Input file not found at {input_file_path}")
        return
    except Exception as e:
        print(f"An error occurred during initial file read: {e}")
        return

    # Second pass: Process each stored chunk for role extraction
    for i, raw_chunk_str in enumerate(all_chunks_raw_str):
        try:
            chunk_data = json.loads(raw_chunk_str)
            chunk_id = chunk_data.get("id", "No ID")

            # NEW: Prepare context for Gemini
            context_chunks_texts = []
            
            # Add preceding chunks (e.g., 2 chunks before)
            # You can adjust `context_window_size` to control how many chunks are included for context
            context_window_size = 2 
            for j in range(max(0, i - context_window_size), i):
                try:
                    # Attempt to parse context chunk to get its 'text' field
                    context_chunk_obj = json.loads(all_chunks_raw_str[j])
                    context_text = context_chunk_obj.get("text", "")
                    if context_text:
                        context_chunks_texts.append(f"Preceding Chunk {context_chunk_obj.get('id', j)}: {context_text}")
                except json.JSONDecodeError:
                    context_chunks_texts.append(f"Preceding Chunk {j}: (Malformed/Unparsable)")
            
            # Add current chunk's text (if 'role' is empty)
            current_text = chunk_data.get("text", "")
            if current_text:
                context_chunks_texts.append(f"Current Chunk {chunk_id}: {current_text}")

            # Add succeeding chunks (e.g., 2 chunks after)
            for j in range(i + 1, min(len(all_chunks_raw_str), i + 1 + context_window_size)):
                try:
                    context_chunk_obj = json.loads(all_chunks_raw_str[j])
                    context_text = context_chunk_obj.get("text", "")
                    if context_text:
                        context_chunks_texts.append(f"Succeeding Chunk {context_chunk_obj.get('id', j)}: {context_text}")
                except json.JSONDecodeError:
                    context_chunks_texts.append(f"Succeeding Chunk {j}: (Malformed/Unparsable)")
            
            # Construct the full prompt for Gemini with context
            # CHANGED: The prompt structure to include context and then the specific chunk to analyze
            full_gemini_prompt = f"""
{system_prompt_template.replace("<ROLES_LIST>", formatted_roles_list)}

Consider the following contextual information from surrounding document chunks:
--- START CONTEXT ---
{"" if not context_chunks_texts else "\\n".join(context_chunks_texts)}
--- END CONTEXT ---

Now, process the following specific JSON chunk to extract its role, filling the 'role' field if empty.
Specific JSON Chunk to Analyze:
{raw_chunk_str}
"""

            # Check if the 'role' field is empty
            if not chunk_data.get("role"):
                # CHANGED: Pass model_temperature to extract_role_string_with_gemini
                identified_role = extract_role_string_with_gemini(full_gemini_prompt, roles_data, temperature_value=model_temperature) 
                
                # Update the 'role' field in the dictionary
                chunk_data["role"] = identified_role
            else:
                print(f"Chunk ID: {chunk_id} already has a role. Skipping API call.")

            updated_chunks.append(chunk_data)

        except json.JSONDecodeError as e:
            print(f"--- JSON DECODE ERROR during processing ---")
            print(f"Error: {e}")
            print(f"Problematic chunk content (during 2nd pass, line {e.lineno}, char {e.pos}):\n{raw_chunk_str}")
            print(f"--- END ERROR CHUNK ---")
            continue 
        except Exception as e:
            print(f"An unexpected error occurred while processing chunk {chunk_id}: {e}\nChunk content:\n{raw_chunk_str}")
            continue
    
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
    
    # NEW: Define the desired temperature
    # For role extraction, a low temperature (e.g., 0.0 to 0.3) is usually best for precision.
    model_temperature = 0.2 

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
        with open(input_file_path, 'w', encoding='utf-8') as f: # Added encoding for dummy file
            f.write(dummy_content.strip())
        print("Dummy file created. You can replace its content with your actual data.")


   # Run the processing
    # CHANGED: Pass model_temperature to process_file_and_extract_roles
    process_file_and_extract_roles(input_file_path, output_file_path, system_prompt_path, roles_data_path, model_temperature=model_temperature) 

    
    print(f"\n--- Content of '{output_file_path}' ---")
    try:
        with open(output_file_path, 'r', encoding='utf-8') as f:
            print(f.read())
    except FileNotFoundError:
        print("Output file not found.")
