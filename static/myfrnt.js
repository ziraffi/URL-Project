// myfrnt.js
// Global variable to store the selected sheet
var selectedSheet = null;
// Flag to track if the file section has been loaded
var fileSectionLoaded = false;
// Flag to track if sheet names have been fetched
var sheetNamesFetched = false;


$(document).ready(function () {
    var windowHeight = $(window).height(); // Get the window height
    var footer = $("footer");
    var header = $("header");
    var lastScrollTop = 0; // Variable to store the last scroll position

    $(window).scroll(function() {
        var scrollPosition = $(this).scrollTop();
        var scrollThreshold = windowHeight * 0.60; // 45% of window height

        // Animation for header
        if (scrollPosition > scrollThreshold || lastScrollTop < scrollPosition) {
            // Hide the header with fade out animation
            header.stop().animate({
                top: '-100px', // Move header off-screen
                opacity: 0
            }, 500);
        } else {
            // Show the header with fade in animation
            header.stop().animate({
                top: '0', // Move header back to its original position
                opacity: 1                
            }, 500);
        }

        // Animation for footer
        if ($(window).scrollTop() > lastScrollTop) {
            if(scrollPosition + $(window).height() >= $(document).height()) {
                // Show the footer with fade in animation
                footer.fadeIn();
            }
        } else {
            // Hide the footer with fade out animation
            footer.fadeOut();
        }
        lastScrollTop = scrollPosition; // Update the last scroll position
    });
 
    // Event listener for toggling between file form and manual form
    $('#toggle_file').on("click", function () {
        $('#manual_form').removeClass('right-side').hide();
        $('#file_form').show().addClass('left-side');
        $('#manual_form').hide();
        $('#url-container').hide();
        $('#manual-data').val('');
    });

    $('#toggle_manual').on("click", function () {
        $('#file_form').removeClass('left-side').hide();
        $('#manual_form').show().addClass('right-side');;
        $('#url-container').hide();
        $('#file').val('');
        $('#sheet-name').empty();
        $('#column-name').empty();
    });

    const openNavButton = $('.fa-bars');
    const closeNavIcon = $('.close-icon');
    const navigation = $('.navigation');

    // Function to open side panel
    function openNav() {
        navigation.addClass('active');
        openNavButton.hide();
        closeNavIcon.show();
    }

    // Function to close side panel
    function closeNav() {
        navigation.removeClass('active');
        openNavButton.show();
        closeNavIcon.hide();
    }

    // Event listener for opening side panel
    openNavButton.on('click', function () {
        openNav();
    });

    // Event listener for closing side panel
    closeNavIcon.on('click', function () {
        closeNav();
    });
    function loadFormSection(sectionName) {
        console.log('Loading form section:', sectionName);

        // Check if the file section has already been loaded
        if (sectionName === 'file_section' && fileSectionLoaded) {
            return;
        }

        $.ajax({
            url: '/templates/' + sectionName + '.html',
            type: 'GET',
            success: function (response) {
                $('#form-container').html(response).show();
                console.log('Form section loaded:', sectionName);
                // Set the flag to true when the file section is loaded
                if (sectionName === 'file_section') {
                    fileSectionLoaded = true;
                }
            },
            error: function (xhr, status, error) {
                console.error('Error loading form section:', error);
                $('#form-container').html('<p>Error loading form.</p>');
            }
        });
    }
    var formSections = ['file_section', 'batch_section', 'dropdown_section', 'output_file_selection'];
    var currentSectionIndex = 0;
    loadFormSection(formSections[currentSectionIndex]);

    function loadNextFormSection() {
        currentSectionIndex++;
        if (currentSectionIndex < formSections.length) {
            loadFormSection(formSections[currentSectionIndex]);
        } else {
            console.log('All form sections loaded.');
        }
    }

    $(document).on('click', '#load-next-section-button', function () {
        console.log('Button clicked');
        loadNextFormSection();
    });
// ***********************************************************************
            // Manual form Section start from here
// ***********************************************************************
    $(document).on('click', '#manual-form-submit', handleManualFormSubmit);

    // Function to handle manual form submission
    function handleManualFormSubmit(event) {
        event.preventDefault();
        const manualData = $('#manual-data').val();
        const selectedSheet = $('#sheet-name').val();
        const selectedColumn = $('#column-name').val();
        // Send manual data to server
        $.ajax({
            url: '/process_manual_input',
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({
                manual_data: manualData,
                selected_sheet: selectedSheet,
                selected_column: selectedColumn
            }),
            success: function (data) {
                $('#valid_list').empty();
                $('#invalid_list').empty(); // Clear invalid list
                $('#url-container').show();
                // Handle server response
                if (data.error_message) {
                    $('#error-message').text(data.error_message);
                } else {
                    // Clear previous data
                    $('#valid_list').empty();
                    $('#invalid_list').empty();
                    // Append column data to URL container
                    appendColumnDataToUrlContainer(data.column_data);
                }
            },
            error: function (error) {
                console.error('Error:', error);
            }
        });
    }

    // Function to append column data to URL container
    function appendColumnDataToUrlContainer(columnData) {
        let validUrlExists = false;
        let invalidDataExists = false;

        // Arrays to store data for each property
        let mnl_data = [];
        let mnl_clmNum = [];
        let mnl_rwNum = [];
        let mnl_shtNum = [];
        const entry_type = ["Entered Data Manually"]

        // Iterate through columnData array
        for (let i = 0; i < columnData.length; i++) {
            const data = columnData[i].data;
            const column_number = columnData[i].column_number;
            const row_number = columnData[i].row_number;
            const sheet_number = columnData[i].sheet_number;

            // Append data to respective arrays if it's a valid URL
            if (testValidURL(data)) {
                mnl_data.push(data);
                mnl_clmNum.push(column_number);
                mnl_rwNum.push(row_number);
                mnl_shtNum.push(sheet_number);
                validUrlExists = true;
            } else {
                // Skip null values
                if (data === null) {
                    continue;
                }
                invalidDataExists = true;
                $('#invalid_list').append(data);
            }
        }

        // Construct the manualDataSet object
        let manualDataSet = {
            data: mnl_data,
            column_number: mnl_clmNum,
            row_number: mnl_rwNum,
            sheet_number: mnl_shtNum,
            choosen: entry_type
        };

        // Append valid URLs to the URL container
        manualDataSet.data.forEach((data, index) => {
            const urlDiv = $('<div>').addClass('url-item');
            urlDiv.text(data);
            urlDiv.attr('sheet_number', manualDataSet.sheet_number[index]);
            urlDiv.attr('row_number', manualDataSet.row_number[index]);
            urlDiv.attr('column_number', manualDataSet.column_number[index]);
            $('#valid_list').append($('<a class="hover-underline-animation"></a>').attr('href', data).text(data));
            $('#valid_list').append('<br>');
        });

        console.log("manualDataSet:", manualDataSet);


        // Show or hide valid_list based on the presence of valid data
        if (validUrlExists) {
            $('#valid_list').prepend($('<h3>Fetched URLs:</h3>'));
            $('#valid_list').show();
        } else {
            $('#valid_list').hide();
        }

        // Show or hide invalid_list based on the presence of invalid data
        if (invalidDataExists) {
            $('#invalid_list').prepend($('<h3>Junk:</h3>'));
            $('#invalid_list').show();
        } else {
            $('#invalid_list').hide();
        }

        if (validUrlExists || invalidDataExists) {
            $('#url-container').show();
        } else {
            $('#url-container').append('<p>No Data Received Please Enter Valid URLs</p>');
        }
    }
// ***********************************************************************
            // Manual form Section end from here
// ***********************************************************************
// Function to check if a string is a valid URL
    function testValidURL(list_url) {
        // Regular expression to validate URLs
        var pattern = new RegExp('^(https?:\\/\\/)?' + // protocol
            '((([a-z\\d]([a-z\\d-]*[a-z\\d])*)\\.)+[a-z]{2,}|' + // domain name
            '((\\d{1,3}\\.){3}\\d{1,3}))' + // OR ip (v4) address
            '(\\:\\d+)?(\\/[-a-z\\d%_.~+]*)*' + // port and path
            '(\\?[;&a-z\\d%_.~+=-]*)?' + // query string
            '(\\#[-a-z\\d_]*)?$', 'i'); // fragment locator
        return pattern.test(list_url);
    }

    // let dataFetched = false; // Flag to track if data has been fetched

// Function to fetch column Data
async function fetchColumnURLs(formData) {
    // Initialize dataSet
    let fileDataSet = {
        data: [],
        column_number: [],
        row_number: [],
        sheet_number: [],
        choosen: [] // Changed from array to single value
    };

    try {
        const response = await fetch('/input_section', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            throw new Error('Failed to fetch column Data');
        }

        const data = await response.json();
        console.log("Received data frequency:", data);
        // Display column Data in the valid_list and invalid_list divs
        $('#valid_list').empty();
        $('#invalid_list').empty(); // Clear invalid list
        $('#url-container').show();

        var raw_data = data.column_data;
        const file_name = data.selected_file;
        if (raw_data && raw_data.length > 0) {
            let validDataExists = false;
            let invalidDataExists = false;

            // Check if choosen is already set
            if (fileDataSet.choosen.length === 0) {
                fileDataSet.choosen.push(file_name);
            }

            raw_data.forEach(item => {
                let list_url = item.data;
                let column_number = item.column_number;
                let row_number = item.row_number;
                let sheet_number = item.sheet_number;

                // Check if the data is a valid URL
                if (testValidURL(list_url)) {
                    // Add data to dataSet
                    fileDataSet.column_number.push(column_number);
                    fileDataSet.row_number.push(row_number);
                    fileDataSet.sheet_number.push(sheet_number);
                    fileDataSet.data.push(list_url);

                    // Display valid URLs
                    $('#valid_list').append($('<a class="hover-underline-animation"></a>').attr('href', list_url).text(list_url));
                    $('#valid_list').append('<br>');
                    validDataExists = true;
                } else {
                    // Skip null values
                    if (list_url === null) {
                        return;
                    }
                    $('#invalid_list').append($('<p></p>').text(list_url));
                    $('#invalid_list').append('<br>');
                    invalidDataExists = true;
                }
            });

            // Show or hide valid_list based on the presence of valid data
            if (validDataExists) {
                $('#valid_list').prepend($('<h3>Fetched URLs:</h3>'));
                $('#valid_list').show();
            } else {
                $('#valid_list').hide();
            }

            // Show or hide invalid_list based on the presence of invalid data
            if (invalidDataExists) {
                $('#invalid_list').prepend($('<h3>Junk:</h3>'));
                $('#invalid_list').show();
            } else {
                $('#invalid_list').hide();
            }

            // Show or hide url-container based on the presence of valid or invalid data
            if (validDataExists || invalidDataExists) {
                $('#url-container').show();
            } else {
                $('#url-container').hide();
            }
        } else {
            $('#valid_list').append($('<p>No URLs found for the selected column.</p>'));
            $('#invalid_list').hide(); // Hide invalid list if no data
            $('#valid_list').hide(); // Hide valid list if no data
            $('#url-container').hide(); // Hide url-container if no data
        }
    } catch (error) {
        console.error('Error fetching column Data:', error);
    }
    console.log("dataSet:", fileDataSet); // Logging the dataSet
    // displayDataSetsInTable(fileDataSet);
}

// Function to display data sets in tabular format
function displayDataSetsInTable(fileDataSet, manualDataSet) {
    // Clear previous tables if any
    $('#file-data-table').empty();
    $('#manual-data-table').empty();

    // Display file data in a table
    displayDataSetInTable(fileDataSet, '#file-data-table', 'File Data');

    // Display manual data in a table
    displayDataSetInTable(manualDataSet, '#manual-data-table', 'Manual Data');
}

// Function to display a data set in a table
function displayDataSetInTable(dataSet, tableId, tableName) {
    const table = $('<table>').addClass('data-table');
    const tableCaption = $('<caption>').text(tableName);
    table.append(tableCaption);

    // Create table headers
    const headersRow = $('<tr>');
    for (let key in dataSet) {
        headersRow.append($('<th>').text(key));
    }
    table.append(headersRow);

    // Create table rows
    for (let i = 0; i < dataSet.data.length; i++) {
        const dataRow = $('<tr>');
        for (let key in dataSet) {
            const cellData = dataSet[key][i];
            dataRow.append($('<td>').text(cellData));
        }
        table.append(dataRow);
    }

    // Append the table to the specified container
    $(tableId).append(table);
}


    // Function to fetch sheet names and column names asynchronously
    function fetchSheetAndColumnNames(formData) {
        try {
            fetch('/input_section', {
                method: 'POST',
                body: formData
            })
                .then(response => {
                    if (!response.ok) {
                        throw new Error('Failed to fetch sheet names and column names');
                    }
                    return response.json();
                })
                .then(data => {
                    console.log('Sheet names and column names fetched successfully:', data);

                    // Update the selected sheet based on the server's response
                    selectedSheet = data.selected_sheet;
                    if (!data.is_csv) {
                        // For XLSX files
                        populateSheetDropdown(selectedSheet, data.sheet_names);
                        // Populate column dropdown with column names for the selected sheet
                        populateColumnDropdown(data.sheet_columns[selectedSheet], selectedSheet, data.column_data);
                        // Update the selected sheet without resetting
                        $('#sheet-name').val(selectedSheet);
                        // Show sheet dropdown for XLSX files
                        $('#sheet-name').show();
                        // Show label for XLSX files
                        $('label[for="sheet-name"]').show();
                    } else {
                        // For CSV files
                        populateColumnDropdown(data.sheet_columns, selectedSheet, data.column_data);
                        // Hide sheet dropdown for CSV files
                        $('#sheet-name').empty().hide();
                        // Hide label for CSV files
                        $('label[for="sheet-name"]').hide();
                    }

                    // Fetch column data for the default selected column
                    var selectedColumn = $('#column-name').val(); // Get the selected column
                    if (selectedColumn) {
                        var formData = new FormData(); // Initialize FormData object
                        formData.append('file', $('#file')[0].files[0]); // Include the file data
                        formData.append('selected_sheet', selectedSheet); // Pass the selected sheet
                        formData.append('selected_column', selectedColumn); // Pass the selected column
                        // Pass the FormData object to fetch column Data
                        fetchColumnURLs(formData);
                    }
                })
                .catch(error => {
                    console.error('Error fetching sheet names and column names:', error);
                });
        } catch (error) {
            console.error('Error fetching sheet names and column names:', error);
        }
    }

    // Function to populate sheet dropdown
    async function populateSheetDropdown(selectedSheet, sheetNames) {
        var sheetDropdown = $('#sheet-name');
        sheetDropdown.empty();
        if (sheetNames && sheetNames.length > 0) {
            $.each(sheetNames, function (_, sheetName) {
                sheetDropdown.append($('<option></option>').val(sheetName).text(sheetName));
            });

            // Set the selected sheet to the first sheet by default if not provided
            if (!selectedSheet) {
                selectedSheet = sheetNames[0];
            }
        } else {
            console.error('No sheet names available.');
            sheetDropdown.append($('<option disabled selected>Please choose a sheet</option>'));
        }
    }

    // Function to populate column dropdown
    async function populateColumnDropdown(columnNames, selectedSheet) {
        var columnDropdown = $('#column-name');
        columnDropdown.empty();

        if (columnNames) {
            $.each(columnNames, function (_, columnName) {
                columnDropdown.append($('<option></option>').val(columnName).text(columnName));
                
            });
        } else {
            console.error('No column names available for the selected sheet:', selectedSheet);
            columnDropdown.append($('<option disabled selected>No columns available</option>'));
        }

        // Get the default selected column
        var selectedColumn = columnDropdown.val();

        // Fetch column data for the default selected column
        if (selectedColumn) {
            console.log("Selected Column:", selectedColumn);
            var formData = new FormData(); // Initialize FormData object
            formData.append('file', $('#file')[0].files[0]); // Include the file data
            formData.append('selected_sheet', selectedSheet); // Pass the selected sheet
            formData.append('selected_column', selectedColumn); // Pass the selected column
            // Pass the FormData object to fetch column Data
            fetchColumnURLs(formData);
        }
    }


    // Handle column dropdown change event
    $(document).on('change', '#column-name', function () {
        // Get the selected column
        var selectedColumn = $(this).val();
        console.log("Selected Column:", selectedColumn);

        // Check if the selected column is not null or empty
        if (selectedColumn) {
            selectedSheet= $('#sheet-name').val();
            var formData = new FormData(); // Initialize FormData object
            formData.append('file', $('#file')[0].files[0]); // Include the file data
            formData.append('selected_sheet', selectedSheet); // Pass the selected sheet
            formData.append('selected_column', selectedColumn); // Pass the selected column
            // Pass the FormData object to fetch column Data
            fetchColumnURLs(formData);
        } else {
            console.log('No valid column selected.');
        }
    });

    // Function to handle sheet dropdown change event
    $(document).on('change', '#sheet-name', function () {
        selectedSheet = $(this).val(); // Update the selected sheet value
        // Construct FormData object with selected sheet value
        var formData = new FormData();
        formData.append('file', $('#file')[0].files[0]); // Include the file data
        formData.append('selected_sheet', selectedSheet); // Use the first sheet if selectedSheet is null
        // Pass the FormData object to fetch sheet and column names
        fetchSheetAndColumnNames(formData);
    });

    // Function to handle file change event
    $(document).on('change', '#file', function () {
        // Display column Data in the valid_list div
        $('#valid_list').empty();
        var fileInput = $(this)[0].files[0];
        console.log("Received File", fileInput, typeof fileInput);
        var formData = new FormData(); // Initialize FormData object

        if (fileInput) {
            formData.append('file', fileInput);

            // Pass the FormData object to fetch sheet and column names
            fetchSheetAndColumnNames(formData);
        } else {
            console.error('No file selected.');
        }
    });
});
