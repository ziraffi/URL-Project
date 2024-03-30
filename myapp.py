from flask import Flask, render_template, request, jsonify, make_response
from io import StringIO,BytesIO
import random
import string
import pandas as pd
import openpyxl
import logging
import asyncio
import pandas as pd
import os
from domain_checker import process_urls_async, progress_info
app = Flask(__name__)


@app.route('/')
def index():
    return render_template('url_Project.html')
@app.route('/login.html')
def login():
    return render_template('login.html')

@app.route('/guide.html')
def guide():
    return render_template('guide.html')

@app.route('/disclaimer.html')
def disclaimer():
    return render_template('disclaimer.html')
@app.route('/privacy_policy.html')
def privacy_policy():
    return render_template('privacy_policy.html')

@app.route('/registration.html')
def register():
    return render_template('register.html')

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
            print("Current File name for CSV Test: ",filename)                   
            return {'sheet_columns': columns, 'column_data': column_data, 'selected_sheet': filename, 'selected_file': filename, 'is_csv': True}    
        elif uploaded_file.filename.endswith(".xlsx"):
            # For Excel files, extract sheet names and column names
            wb = openpyxl.load_workbook(filename=BytesIO(file_contents), data_only=True)
            sheet_names = wb.sheetnames
            sheet_columns = {}
            column_data = []
            selected_file= uploaded_file.filename.split('.')[0]            
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
            return { 'selected_file': selected_file,'sheet_names': sheet_names, 'sheet_columns': sheet_columns, 'column_data': column_data, 'column_titles': column_titles, 'selected_sheet': selected_sheet, 'selected_column': selected_column, 'is_csv': False}
        else:
            return {'error_message': "Unsupported file format"}

    except Exception as e:
        return {'error_message': f"Error processing file: {str(e)}"}

# Set up logging configuration
logging.basicConfig(level=logging.DEBUG)  # Set the logging level to DEBUG

# Define function to process dataSet containing URLs asynchronously
async def process_dataSet_urls(urlSet, semaphore):
    try:
        if not urlSet or 'url_list' not in urlSet:
            logging.error("Empty or missing 'url_list' key in urlSet")
            yield jsonify({'error': 'Missing data in request'})
        else:
            urls = urlSet['url_list']
            logging.info(f"Processing {len(urls)} URLs asynchronously")
            async for stats in process_urls_async(urls, semaphore):
                yield stats
    except Exception as e:
        logging.error(f"Error processing URLs: {e}")
        yield jsonify({'error': str(e)})

def generate_unique_filename(base_filename):
    directory = os.path.dirname(base_filename)
    filename = os.path.basename(base_filename)
    
    if not os.path.exists(base_filename):
        return base_filename  # If the file doesn't exist, use the base filename

    # If the file exists, generate a unique filename
    alphabet_hex = ''.join(random.choice(string.hexdigits) for _ in range(8))  # Generate a random hexadecimal code
    unique_filename = f"rk-{alphabet_hex}-{filename}"
    return os.path.join(directory, unique_filename)

@app.route('/process_url_data', methods=['POST', 'GET'])
async def process_clienturl_data():
    try:
        # Ensure request contains JSON data
        if not request.is_json:
            return jsonify({'error': 'Request content must be in JSON format'})

        url_set = request.json

        app.logger.info(f"Received dataSet: {url_set} (type: {type(url_set)})")

        # Run asynchronous tasks to process URLs
        semaphore = asyncio.Semaphore(10)  # Adjust the semaphore value as needed
        logging.info("Starting URL processing")

        data = []
        async for result in process_urls_async(url_set['url_list'], semaphore):
            if 'domain_info' in result:
                data.append(result)

        logging.info("URL processing completed")

        # Convert data to DataFrame (if needed)
        if data:
            print("Server Returning Data", data)
            result_df = pd.DataFrame(data)
            domain_info_df = result_df['domain_info'].apply(pd.Series)

            # Convert Expiration Date to datetime objects and make them timezone-aware (if needed)
            if 'Expiration Date' in domain_info_df.columns:
                domain_info_df['Expiration Date'] = pd.to_datetime(domain_info_df['Expiration Date'], unit='ms').dt.tz_localize('UTC').dt.tz_convert('Asia/Kolkata')

            # Save domain information as CSV (if data exists)
            if not domain_info_df.empty:
                csv_filename = 'rk.csv'
                unique_csv_filename = generate_unique_filename(csv_filename)

                # Save DataFrame as CSV using the unique filename
                domain_info_df.to_csv(unique_csv_filename, index=False)

                return jsonify({
                    'message': 'URL data processed successfully',
                    'has_downloadable_data': True,
                    'data': result_df.to_json(orient='records'),
                    'csv_filename': unique_csv_filename,  # Send the filename to the client
                    
                })
            else:
                return jsonify({'error': 'No domain information available to download'})

        else:
            logging.error("No data retrieved")
            return jsonify({'error': 'No data retrieved'})

    except Exception as e:
        logging.error(f"Error processing URL data: {e}")
        return jsonify({'error': str(e)})
    
@app.route('/progress', methods=['POST'])
def get_progress():
    # print("At the End Point: ", progress_info)
    return jsonify(progress_info)
    
@app.route('/download/<csvFilename>', methods=['GET'])
def download_csv(csvFilename):
    try:
        csv_path = f'\\opt\\render\\project\\src\\{csvFilename}'  # Update with the actual path to your CSV directory
        
        # Check if the file exists
        if os.path.exists(csv_path):
            # Open the file in binary mode
            with open(csv_path, 'rb') as file:
                # Create a Flask response object
                response = make_response(file.read())
                
            # Set the appropriate content type for CSV files
            response.headers.set('Content-Type', 'text/csv')
            # Set the Content-Disposition header to specify the filename
            response.headers.set('Content-Disposition', f'attachment; filename={csvFilename}')
            
            return response
        else:
            return jsonify({'error': 'File not found'})
    except Exception as e:
        return jsonify({'error': str(e)})

def list_files_in_directory(directory):
    try:
        # Get the list of files and folders in the specified directory
        files_and_folders = os.listdir(directory)
        
        # Print each file and folder
        for item in files_and_folders:
            print(item)
    except OSError as e:
        print(f"Error: {e}")

# Specify the home directory path
home_directory = "/opt/render/project/src"

# List files and folders in the home directory
list_files_in_directory(home_directory)

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

