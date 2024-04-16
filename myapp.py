from flask import Flask, render_template, request, jsonify, make_response, Response, send_from_directory
import json
from io import StringIO,BytesIO
import random
import string
import pandas as pd
import openpyxl
import logging
import asyncio
import pandas as pd
import os
import uuid
from domain_checker import process_urls_async, progress_info
app = Flask(__name__)
# @app.route('/login.html')
# def login():
#     return render_template('login.html')

# @app.route('/registration.html')
# def register():
#     return render_template('register.html')

# Dictionary to store user consent status with their unique identifiers
user_consent_status = {}

@app.route('/')
def index():
    return render_template('url_Project.html')

@app.route('/robots.txt')
def robots():
    return send_from_directory('static', 'robots.txt')

@app.route('/sitemap.xml')
def sitemapxml():
    response= make_response(send_from_directory('static', 'sitemap.xml'))
    response.headers['Content-Type'] = 'application/xml'
    return response

@app.route('/sitemap.html')
def sitemaphtml():
    return send_from_directory('static', 'sitemap.html')

@app.route('/set-cookie', methods=['POST'])
def set_cookie():
    user_id = str(uuid.uuid4())  # Generate a unique identifier for the user
    user_consent_status[user_id] = True  # Set consent status for the user
    
    # Prepare JSON object
    data = {
        'user_id': user_id,
        'cookie_consent': request.cookies.get('cookie_consent')
    }
    
    # Append data to JSON file
    cookie_store = '/opt/render/project/src/storage'  # Assuming cookie_store is a directory
    json_file = os.path.join(cookie_store, 'cookie_data.json')
    
    if not os.path.exists(json_file):
        with open(json_file, 'w') as f:
            json.dump([data], f, indent=4)  # Initialize file with a list containing the first data object
    else:
        with open(json_file, 'r+') as f:
            try:
                existing_data = json.load(f)
            except json.decoder.JSONDecodeError:
                existing_data = []
                
            existing_data.append(data)  # Add new data to existing list
            f.seek(0)  # Move the file pointer to the beginning
            json.dump(existing_data, f, indent=4)  # Write JSON data with proper formatting
    
    response = make_response()
    response.set_cookie('user_id', user_id, max_age=365*24*60*60)  # Set cookie with the user's identifier
    response.set_cookie('cookie_consent', 'true', max_age=365*24*60*60)  # Set cookie with consent
    
    return response

@app.route('/blog1.html')
def blogone():
    return render_template('blog1.html')
@app.route('/guide.html')
def guide():
    return render_template('guide.html')

@app.route('/favicon.ico')
def favicon():
    return 'dummy', 200
@app.route('/disclaimer.html')
def disclaimer():
    return render_template('disclaimer.html')

@app.route('/privacyPolicy.html')
def privacy_policy():
    return render_template('privacyPolicy.html')

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

def generate_unique_filename(base_filename):
    directory = os.path.dirname(base_filename)
    filename = os.path.basename(base_filename)
    
    if not os.path.exists(base_filename):
        return base_filename  # If the file doesn't exist, use the base filename

    # If the file exists, generate a unique filename
    alphabet_hex = ''.join(random.choice(string.hexdigits) for _ in range(8))  # Generate a random hexadecimal code
    unique_filename = f"rk-{alphabet_hex}-{filename}"
    return os.path.join(directory, unique_filename)

import os
from flask import request, jsonify

@app.route('/process_url_data', methods=['POST'])
async def process_clienturl_data():
    try:
        # Ensure request contains JSON data
        if not request.is_json:
            return jsonify({'error': 'Request content must be in JSON format'})

        cliData = request.json
        url_set = cliData.get('clientUrlSet')
        cancelFlag = cliData.get('cancelFlag')  # Retrieve cancelFlag from the request data

        # Check if the processing should be canceled based on cancelFlag
        if cancelFlag:
            # Return a response indicating that the process was canceled
            return jsonify({'message': 'URL processing canceled'})

        # Run asynchronous tasks to process URLs
        semaphore = asyncio.Semaphore(8)  # Adjust the semaphore value as needed
        logging.info("Starting URL processing")

        data = []
        async for result in process_urls_async(url_set['url_list'], semaphore, cancelFlag):
            if 'domain_info' in result:
                data.append(result)

            # Check if processing is canceled after each iteration
            if cancelFlag:
                break  # Break the loop if processing is canceled

        logging.info("URL processing completed")

        # Convert data to DataFrame (if needed)
        if data:
            result_df = pd.DataFrame(data)
            domain_info_df = result_df['domain_info'].apply(pd.Series)

            # Convert 'Status Code' and 'Response Message' columns from arrays to strings
            if 'Status Code' in domain_info_df.columns:
                domain_info_df['Status Code'] = domain_info_df['Status Code'].apply(array_to_string)
            if 'Response Message' in domain_info_df.columns:
                domain_info_df['Response Message'] = domain_info_df['Response Message'].apply(array_to_string)
                
            # Convert Expiration Date to datetime objects and make them timezone-aware (if needed)
            if 'Expiration Date' in domain_info_df.columns:
                domain_info_df['Expiration Date'] = pd.to_datetime(domain_info_df['Expiration Date'], unit='ms').dt.tz_localize('UTC').dt.tz_convert('Asia/Kolkata')

            # Save domain information as CSV (if data exists)
            if not domain_info_df.empty:
                csv_filename = 'rk.csv'
                unique_csv_filename = generate_unique_filename(csv_filename)

                # Save DataFrame as CSV to the temporary volume (--tmpfs)
                tmpfs_path = '/opt/render/project/src/storage/downloads'  # Path to the temporary volume
                tmp_csv_path = os.path.join(tmpfs_path, unique_csv_filename)
                domain_info_df.to_csv(tmp_csv_path, index=False)
                
                # Get the full path of the saved CSV file
                current_directory = os.path.join(os.getcwd())

                return jsonify({
                    'message': 'URL data processed successfully',
                    'has_downloadable_data': True,
                    'data': result_df.to_json(orient='records'),
                    'csv_filename': unique_csv_filename,  # Send the filename to the client
                    'current_directory': current_directory  # Send the full path to the client
                })
            else:
                return jsonify({'error': 'No domain information available to download'})

        else:
            logging.error("No data retrieved")
            return jsonify({'error': 'No data retrieved'})

    except Exception as e:
        logging.error(f"Error processing URL data: {e}")
        return jsonify({'error': str(e)})

# Define function to convert arrays to strings
def array_to_string(arr):
    return ', '.join(map(str, arr))
    
@app.route('/progress', methods=['POST'])
async def get_progress():
    cancelFlag = request.json.get('cancelFlag')
    if cancelFlag:
        print("cancelFlag At Progress Endpoint: ", cancelFlag)
        # Call the process_urls_async function with only the cancelFlag
        async for data in process_urls_async({}, {}, cancelFlag):
            pass  # Process the data if needed, or you can simply iterate through it
        return jsonify(progress_info)
    # If cancelFlag is not set, return the progress_info as it is
    return jsonify(progress_info)

@app.route('/download/<csvFilename>', methods=['POST'])
def download_csv(csvFilename):
    try:
        # Get the filePath from the request
        filePath = '/opt/render/project/src/storage/downloads'

        # Construct the full path to the CSV file
        csv_path = os.path.join(filePath, csvFilename)
        print("File Path with File name: ", csv_path)
        app.logger.info(f"File Path with File name: {csv_path}")  # Fixed the syntax error here

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



def list_files_in_directory(current_directory,home_directory):
    try:
        # Get the list of files and folders in the specified directory
        files_and_folders = os.listdir(current_directory)
        print("Current directory:", current_directory)
        print("Home directory:", home_directory)
        # Print each file and folder
        for item in files_and_folders:
            print(item)
    except OSError as e:
        print(f"Error: {e}")

# Specify the home directory path
home_directory = os.path.expanduser('~')
current_directory = os.getcwd()

# List files and folders in the home directory
list_files_in_directory(current_directory,home_directory)

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
