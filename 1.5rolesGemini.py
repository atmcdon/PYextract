import json
import google.generativeai as genai
import os # For accessing environment variables

# --- Configuration ---
# IMPORTANT: Replace with your actual Gemini API key or set as an environment variable
# It's highly recommended to use environment variables for API keys for security
try:
    genai.configure(api_key=os.environ["GEMINI_API_KEY"])
except KeyError:
    print("Error: GEMINI_API_KEY environment variable not set.")
    print("Please set the GEMINI_API_KEY environment variable or replace 'os.environ[\"GEMINI_API_KEY\"]' with your actual key.")
    exit()

# Initialize the Gemini model
model = genai.GenerativeModel('gemini-pro')

def extract_role_with_gemini(text_chunk):
    """
    Uses the Gemini API to extract the 'role' from a given text chunk.

    Args:
        text_chunk (str): The text content containing the role information.

    Returns:
        str: The extracted role, or None if not found or an error occurs.
    """
    prompt = f"""
    Given the following JSON-like text, identify and extract the value associated with the key "role".
    If the "role" key is present, provide only its value. If it's not present or if the value is empty, state "Role not found".

    Example input:
    {{
        "id": "chunk_230",
        "role": "Source: reformatted_single_line_sections.txt",
        "header": "2.3.1.1",
        "text": "Serve as decision authority for all AFR assignment requests that are not addressed within this instruction.",
        "preceding_header_ids": ["2.3.1"],
        "preceding_chunk_ids": ["chunk_226", "chunk_227"]
    }}

    Example output:
    Source: reformatted_single_line_sections.txt

    Example input:
    {{
        "id": "chunk_231",
        "header": "2.3.2",
        "text": "Headquarters Air Force Reserve Command (AFRC), Chief, Military Personnel Division (AIK) is the OPR for Assignment of Personnel Assigned to AFR and will:",
        "preceding_chunk_ids": ["chunk_226"]
    }}

    Example output:
    Role not found

    Now, process the following text:
    {text_chunk}
    """
    try:
        response = model.generate_content(prompt)
        # Assuming the API directly returns the role or "Role not found"
        # You might need to adjust this based on the actual API response format
        return response.text.strip()
    except Exception as e:
        print(f"Error calling Gemini API: {e}")
        return None

def process_file_and_extract_roles(file_path):
    """
    Reads the file, extracts JSON chunks, and finds roles using Gemini.

    Args:
        file_path (str): The path to the input file.

    Returns:
        list: A list of dictionaries, each containing 'id' and 'role'.
    """
    extracted_roles = []
    current_chunk_str = ""
    brace_count = 0
    in_chunk = False

    try:
        with open(file_path, 'r') as f:
            for line in f:
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
                                chunk_id = chunk_data.get("id", "No ID")

                                # Now, send the whole chunk string to Gemini for role extraction
                                role = extract_role_with_gemini(current_chunk_str)
                                extracted_roles.append({"id": chunk_id, "role": role})

                            except json.JSONDecodeError as e:
                                print(f"Error decoding JSON chunk: {e}\nChunk content:\n{current_chunk_str}")
                            except Exception as e:
                                print(f"An unexpected error occurred while processing chunk: {e}\nChunk content:\n{current_chunk_str}")
                            finally:
                                current_chunk_str = ""
                                in_chunk = False
                                brace_count = 0
                    else:
                        # Handle potential nested braces if your JSON can have them
                        # For simple flat JSON, this might not be strictly necessary
                        brace_count += stripped_line.count('{')
                        brace_count -= stripped_line.count('}')

    except FileNotFoundError:
        print(f"Error: File not found at {file_path}")
    except Exception as e:
        print(f"An error occurred: {e}")

    return extracted_roles

# --- Main execution ---
if __name__ == "__main__":
    # Replace 'your_file.txt' with the actual path to your text file
    # derived from the image (e.g., if you copy-pasted the content)
    file_path = 'parsed_document_chunks.txt' # Assuming you saved the content as this file name

    # Create a dummy file for demonstration purposes if it doesn't exist
    if not os.path.exists(file_path):
        print(f"Creating a dummy file '{file_path}' for demonstration.")
        dummy_content = """
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
"role": "Source: reformatted_single_line_sections.txt",
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
"header": "2.3.9.2",
"text": "Provide guidance and documentation instructions to the MPF for unit program.",
"preceding_chunk_ids": ["chunk_231"]
}
"""
        with open(file_path, 'w') as f:
            f.write(dummy_content.strip())
        print("Dummy file created. You can replace its content with your actual data.")


    results = process_file_and_extract_roles(file_path)

    print("\n--- Extracted Roles ---")
    for item in results:
        print(f"Chunk ID: {item['id']}, Role: {item['role']}")