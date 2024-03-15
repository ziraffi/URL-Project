from flask import Flask, render_template, request, jsonify
import pandas as pd
from io import StringIO,BytesIO
import openpyxl
import logging
import asyncio
import pandas as pd
import os
import pytz
from domain_checker import process_urls_async
app = Flask(__name__)

@app.route('/')
def index():
    return render_template('url_Project.html')
@app.route('/login.html')
def login():
    return render_template('login.html')

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
            return {'sheet_columns': columns, 'column_data': column_data, 'selected_sheet': filename, 'is_csv': True}                       
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
# logging.basicConfig(level=logging.DEBUG)  # Set the logging level to DEBUG

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


# Define route to process urlSet data from the client
@app.route('/process_url_data', methods=['POST', 'GET'])
async def process_clienturl_data():
    try:
        # Get the dataSet from the request
        urlSet = request.json

        app.logger.info(f"Received dataSet: {urlSet} (type: {type(urlSet)})") 
        
        # Run asynchronous tasks to process URLs
        semaphore = asyncio.Semaphore(8)  # Adjust the semaphore value as needed
        # logging.info("Starting URL processing")
        data = []
        async for stats in process_dataSet_urls(urlSet, semaphore):        
            # Process statistics or yield them to the client
            data.append(stats)  # Collect statistics
        # logging.info("URL processing completed")

        # Convert the collected data to JSON
        result_json = jsonify(data)

        # Convert the result JSON data to a DataFrame (if needed)
        result_df = pd.DataFrame(data)

        # Convert the result DataFrame to JSON
        result_json = result_df.to_json(orient='records')

        # Extract the 'domain_info' data from the DataFrame
        domain_info_df = result_df['domain_info'].apply(pd.Series)

        # Define the IST timezone
        ist_tz = pytz.timezone('Asia/Kolkata')
        # Save the 'domain_info' DataFrame to a CSV file
        if not domain_info_df.empty:
            
            output_file_path = 'domain_info.csv'
            count = 1
            while os.path.exists(output_file_path):
                output_file_path = f'domain_info_{count}.csv'
                count += 1

            # Convert Expiration Date to datetime objects and make them timezone-aware
            domain_info_df['Expiration Date'] = pd.to_datetime(domain_info_df['Expiration Date'], unit='ms').dt.tz_localize('UTC').dt.tz_convert(ist_tz)

            domain_info_df.to_csv(output_file_path, index=False)
            
            logging.info(f"Results saved to {output_file_path}")
            return jsonify({'message': 'URL data processed successfully', 
                            'output_file': output_file_path,
                            'data': result_json})

        else:
            logging.error("No data retrieved")
            return jsonify({'error': 'No data retrieved'})
    except Exception as e:
        logging.error(f"Error processing URL data: {e}")
        return jsonify({'error': str(e)})


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
