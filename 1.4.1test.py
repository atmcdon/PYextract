# --- Diagnostic Script ---
# Purpose: To find and print any line containing a '/' from your input file.

input_filename = 'reformatted_single_line_sections.txt' # Make sure this is your correct filename

try:
    with open(input_filename, 'r', encoding='utf-8') as file:
        print("--- Searching for lines with '/' ---")
        found_line = False
        for i, line in enumerate(file):
            if '/' in line:
                print(f"Line {i+1}: {line.strip()}") # .strip() cleans up extra whitespace for readability
                found_line = True
        
        if not found_line:
            print("No lines containing '/' were found in the file.")
        print("--- End of search ---")

except FileNotFoundError:
    print(f"Error: The input file '{input_filename}' was not found.")