from flask import Flask, render_template, request, jsonify
import pandas as pd
from io import StringIO,BytesIO
import openpyxl

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('url_Project.html')

@app.route('/templates/<section_name>.html')
def serve_template(section_name):
    return render_template(f'{section_name}.html'),200

@app.route('/input_section', methods=['POST'])
def file_section():
    uploaded_file = request.files.get('file')
    selected_sheet = request.form.get('selected_sheet')  # Retrieve selected sheet from form data
    selected_column = request.form.get('selected_column')  # Retrieve selected column from form data
    
        # Pass selected sheet and column to process_file
    response_data = process_file(uploaded_file, selected_sheet, selected_column)

    if response_data:
        return jsonify(response_data)
    else:
        return jsonify({'error_message': "No file uploaded"})
@app.route('/process_manual_input', methods=['POST'])
def process_manual_input():
    try:
        # Extract data from the request
        data = request.get_json()
        manual_data = data['manual_data']
        selected_sheet = data['selected_sheet']
        selected_column = data['selected_column']
        
        # Split manual data by newline and remove empty lines
        manual_lines = manual_data.strip().split('\n')
        manual_lines = [line.strip() for line in manual_lines if line.strip()]
        
        # Convert manual data to CSV format
        manual_csv = '\n'.join([f'"{line.replace(",", "")}"' for line in manual_lines])
        
        # Create DataFrame from manual CSV data
        df = pd.read_csv(StringIO(manual_csv), header=None, names=[selected_column])
        
        # Extract column data with additional information
        column_data = [{'data': val, 'sheet_number': 1, 'row_number': idx + 2, 'column_number': 1} for idx, val in enumerate(df[selected_column].tolist()) if pd.notna(val)]
        
        return jsonify({
            'column_data': column_data,
            'is_manual': True
        })
    except Exception as e:
        return jsonify({'error_message': f"Error processing manual input: {str(e)}"}), 500

def process_file(uploaded_file, selected_sheet, selected_column):
    if not uploaded_file:
        return {'error_message': "No file uploaded"}

    try:
        file_contents = uploaded_file.read()
        if uploaded_file.filename.endswith(".csv"):
            # For CSV files, use the file name as the sheet name
            filename = uploaded_file.filename.split('.')[0]
            # Extract column names directly from CSV file
            df = pd.read_csv(BytesIO(file_contents))
            columns = list(df.columns)
            selected_column = selected_column or columns[0]  # Use the first column by default
            # Get URLs for the selected column
            column_data = [{'data': val, 'sheet_number': 1, 'row_number': idx + 2, 'column_number': 1} for idx, val in enumerate(df[selected_column].tolist()) if pd.notna(val)]
            return {'sheet_columns': columns, 'column_data': column_data, 'selected_sheet': filename, 'is_csv': True}
        elif uploaded_file.filename.endswith(".xlsx"):
            # For Excel files, extract sheet names and column names
            wb = openpyxl.load_workbook(filename=BytesIO(file_contents), data_only=True)
            sheet_names = wb.sheetnames
            sheet_columns = {}
            column_data = []
            # Set a default value for selected sheet and column if not provided
            selected_sheet = selected_sheet or sheet_names[0]
            for sheet_number, sheet_name in enumerate(sheet_names, start=1):
                sheet = wb[sheet_name]
                max_row = sheet.max_row
                max_col = sheet.max_column
                column_titles = []
                # Find the selected column
                if sheet_name == selected_sheet:
                    for column_number in range(1, max_col + 1):  # Loop through the columns
                        cell_obj = sheet.cell(row=1, column=column_number)  # Access the first row for column names
                        column_title = cell_obj.value
                        if column_title is None:
                            column_title = f"Column_{column_number}"  # Assign a default title for None values
                        column_titles.append(column_title)

                    if selected_column is None:
                        selected_column = column_titles[0]  # Use the first column by default

                    # Check if the selected column exists
                    if selected_column not in column_titles:
                        return {'error_message': f"Selected column '{selected_column}' not found in sheet '{selected_sheet}'."}

                    # Retrieve data for the selected column along with row numbers
                    column_index = column_titles.index(selected_column) + 1

                    column_data = [{'data':sheet.cell(row=j, column=column_index).value,
                                    'sheet_number': sheet_number,
                                    'row_number': j,
                                    'column_number': column_index}
                                    for j in range(2, max_row + 1)if sheet.cell(row=j, column=column_index).value]
                    # Update selected_column if it matches the current column title
                    selected_column = column_titles[column_index - 1]

                sheet_columns[sheet_name] = column_titles
            
            # Return the processed data
            return {'sheet_names': sheet_names, 'sheet_columns': sheet_columns, 'column_data': column_data, 'column_titles': column_titles, 'selected_sheet': selected_sheet, 'selected_column': selected_column, 'is_csv': False}
        else:
            return {'error_message': "Unsupported file format"}
    except Exception as e:
        return {'error_message': f"Error processing file: {str(e)}"}


@app.route('/submit', methods=['POST'])
def submit_form():
    file_type = request.form.get('file')
    batch = request.form.get('batch')
    url_column = request.form.get('url-column')
    selected_sheet = request.form.get('sheet-name')
    selected_column = request.form.get('column-name')
    required_data = request.form.get('required-data')
    output_file_type = request.form.get('output-file-type')

    print(f"File type: {file_type}, Batch: {batch}, URL column: {url_column}, Selected Sheet: {selected_sheet}, Selected Column: {selected_column}, Required data: {required_data}, Output file type: {output_file_type}")
    return 'Form submitted successfully'

if __name__ == '__main__':
    app.run(debug=True)
