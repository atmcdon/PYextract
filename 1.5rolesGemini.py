import json
import google.generativeai as genai
import os
from dotenv import load_dotenv

# --- Configuration ---
load_dotenv() 

try:
    genai.configure(api_key=os.environ["GEMINI_API_KEY"]) 
except KeyError:
    print("Error: GEMINI_API_KEY not found. Please ensure it's set in your .env file or as an environment variable.")
    exit()

# Initialize the Gemini model
model = genai.GenerativeModel('gemini-1.5-flash')

# ... (other functions: load_roles_data, load_system_prompt_template, format_roles_for_prompt) ...


# CHANGED: Added temperature_value parameter
def extract_role_string_with_gemini(full_context_prompt_text, roles_data, temperature_value=0.2): 
    
    # Args:
        # full_context_prompt_text (str): The complete prompt text including system instructions, roles data,
        #                                  and the current chunk plus its surrounding context.
        # roles_data (list): The list of dictionaries containing role names and abbreviations.
        # temperature_value (float): NEW - The temperature setting for the model. Defaulted to 0.2 for precise extraction.

    # Returns:
        # str: The extracted role string, or "Role not found" if not identified or an error occurs.
    
    # No changes to formatted_roles_list as it's part of full_context_prompt_text now
    
    # NEW: Create a GenerationConfig object
    generation_config = genai.GenerationConfig(
        temperature=temperature_value,
        # You can add other parameters here if needed, e.g., top_p, top_k, max_output_tokens
        # top_p=0.95, # Example: sample from top 95% probability mass
        # top_k=60,   # Example: sample from top 60 most likely tokens
        # max_output_tokens=100 # Example: limit the length of the output
    )

    try:
        # CHANGED: Pass generation_config to generate_content
        response = model.generate_content(
            contents=[
                {"role": "user", "parts": [{"text": full_context_prompt_text}]}
            ],
            generation_config=generation_config
        )
        # Gemini's response should now be just the role string
        return response.text.strip()
    except Exception as e:
        print(f"Error calling Gemini API: {e}")
        return "Role not found" # Default if API call fails


def process_file_and_extract_roles(input_file_path, output_file_path, system_prompt_path, roles_data_path, model_temperature=0.2): # CHANGED: Added model_temperature
    # ... (rest of the function's initial setup and first pass remain the same) ...

    # Second pass: Process each stored chunk for role extraction
    for i, raw_chunk_str in enumerate(all_chunks_raw_str):
        try:
            chunk_data = json.loads(raw_chunk_str)
            chunk_id = chunk_data.get("id", "No ID")

            # ... (context gathering logic remains the same) ...
            
            # Construct the full prompt for Gemini with context
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
    
    # ... (write updated chunks to output file remains the same) ...


# --- Main execution ---
if __name__ == "__main__":
   
    input_file_path = 'parsed_document_chunks copy.txt' 
    output_file_path = 'updated_parsed_document_chunks.txt' 
    roles_data_path = 'roles.json' 
    system_prompt_path = 'system_prompt.txt' 
    
    # NEW: Define the desired temperature
    # For role extraction, a low temperature (e.g., 0.0 to 0.3) is usually best for precision.
    model_temperature = 0.2 

    # dummy data creation for demonstration purposes (remains the same) ...

   # Run the processing
    # CHANGED: Pass model_temperature to process_file_and_extract_roles
    process_file_and_extract_roles(input_file_path, output_file_path, system_prompt_path, roles_data_path, model_temperature=model_temperature) 

    # ... (print output file content remains the same) ...
