from flask import Flask, render_template, request, send_file, jsonify
import itertools
import os
import time

app = Flask(__name__)

# Function to generate combinations with an exact character length
def save_combinations_to_files(password_list, char_length, num_files, output_dir):
    if not char_length or char_length < 1:
        raise ValueError("Character length must be a positive integer.")

    file_paths = []
    file_handlers = []

    # Create file handlers for output files
    for i in range(num_files):
        file_path = os.path.join(output_dir, f"password_combinations_{i + 1}.txt")
        file_handlers.append(open(file_path, 'w'))
        file_paths.append(file_path)

    file_index = 0
    combination_count = 0

    # Generate combinations of specified character length
    for length in range(1, len(password_list) + 1):
        for combination in itertools.permutations(password_list, length):
            combined = ''.join(combination)
            if len(combined) == char_length:  # Ensure the exact character length
                file_handlers[file_index].write(combined + '\n')
                file_index = (file_index + 1) % num_files  # Distribute evenly across files
                combination_count += 1

    # Close file handlers
    for handler in file_handlers:
        handler.close()

    return file_paths, combination_count

@app.route('/', methods=['GET', 'POST'])
def index():
    file_links = []
    error = None
    combination_count = 0
    success = False

    if request.method == 'POST':
        user_input = request.form.get('passwords', '')
        num_files = int(request.form.get('num_files', 1))
        char_length = int(request.form.get('char_length', 0))

        if user_input and char_length > 0:
            passwords = [password.strip() for password in user_input.split(',')]
            desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
            os.makedirs(desktop_path, exist_ok=True)

            # Save combinations to multiple files
            try:
                file_paths, combination_count = save_combinations_to_files(
                    passwords, char_length, num_files, desktop_path
                )
                # Extract just filenames for template
                file_links = [os.path.basename(path) for path in file_paths]
                success = True
            except ValueError as ve:
                error = str(ve)
            except Exception as e:
                error = f"An error occurred: {e}"

    return render_template(
        'index.html', 
        file_links=file_links, 
        error=error, 
        combination_count=combination_count,
        success=success
    )

@app.route('/download/<filename>')
def download_file(filename):
    desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
    file_path = os.path.join(desktop_path, filename)
    
    # Security check - only allow files that start with "password_combinations_"
    if not filename.startswith("password_combinations_") or not filename.endswith(".txt"):
        return "Invalid file request!", 404
        
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True, download_name=filename)
    return "File not found!", 404

@app.route('/api/estimate', methods=['POST'])
def estimate_combinations():
    """API endpoint to estimate number of combinations"""
    data = request.get_json()
    passwords = data.get('passwords', [])
    char_length = data.get('char_length', 0)
    
    if not passwords or char_length < 1:
        return jsonify({'error': 'Invalid input'}), 400
    
    # Estimate combinations (simplified calculation)
    estimate = 0
    for length in range(1, len(passwords) + 1):
        # Calculate permutations for this length
        perm_count = 1
        for i in range(length):
            perm_count *= (len(passwords) - i)
        estimate += perm_count
    
    return jsonify({'estimate': min(estimate, 1000000)})  # Cap at 1M for display

if __name__ == '__main__':
    app.run(debug=True)