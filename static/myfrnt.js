// myfrnt.js
// Global variable to store the selected sheet
// var selectedSheet = null;
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

        $('#manual-data-table').empty();
        $('#mnl-tbl').hide();

    });

    $('#toggle_manual').on("click", function () {
        $('#file_form').removeClass('left-side').hide();
        $('#manual_form').show().addClass('right-side');;
        $('#url-container').hide();
        $('#file').val('');
        $('#sheet-name').empty();
        $('#column-name').empty();
        $('#file-data-table').empty();
        $('#file-tbl').hide();
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
    $('#valid_list').empty();
    $('#invalid_list').empty();
    // Arrays to store data for each property
    let mnl_data = [];
    let mnl_clmNum = [];
    let mnl_rwNum = [];
    let mnl_shtNum = [];
    const entry_type = ["Entered Data Manually"];

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
            $('#valid_list').append($('<a class="hover-underline-animation"></a>').attr('href', data).text(data));
            $('#valid_list').append('<br>');
        } else {
            // Check if the data is empty
            if (data.trim() !== '') {
                invalidDataExists = true;
                $('#invalid_list').append($('<p></p>').text(data));
            }
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

    // Show or hide valid_list based on the presence of valid data
    if (validUrlExists) {
        console.log("manualDataSet:", manualDataSet);
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
    if (validUrlExists || invalidDataExists) {
        $('#url-container').show();
    } else {
        $('#url-container').hide();
    }
    // if (manualDataSet && Object.keys(manualDataSet).length !== 0) {
    //     displayDataSetsInTable(null,manualDataSet);
    // }
    if (manualDataSet && manualDataSet.data && manualDataSet.data.length !== 0) {
        displayDataSetsInTable(null, manualDataSet);
    } else{
        $('#manual-data-table').empty();
        $('#mnl-tbl').hide();
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

// Function to fetch column Data
async function fetchColumnURLs(formData) {
    // Initialize dataSet
    let fileDataSet = {
        data: [],
        column_number: [],
        row_number: [],
        sheet_number: [],
        choosen: [] 
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
        // Display column Data in the valid_list and invalid_list divs
        $('#valid_list').empty();
        $('#invalid_list').empty(); 
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
                    invalidDataExists = true;
                }
            });
            // Show or hide valid_list based on the presence of valid data
            if (validDataExists) {
                $('#valid_list').prepend($('<h3>Fetched URLs:</h3>'));
                $('#valid_list').show();
                console.log("dataSet:", fileDataSet); // Logging the dataSet
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
            $('#invalid_list').append($('<p>No URLs found for the selected column.</p>'));
            $('#invalid_list').show(); // Hide invalid list if no data
            $('#valid_list').hide(); // Hide valid list if no data
            $('#url-container').show(); // Hide url-container if no data
        }
    } catch (error) {
        console.error('Error fetching column Data:', error);
    }
    if (fileDataSet && fileDataSet.data && fileDataSet.data.length !== 0) {
        displayDataSetsInTable(fileDataSet, null);
    } else{
        $('#file-data-table').empty();
        $('#file-tbl').hide();
    }   
}
function displayDataSetsInTable(fileDataSet, manualDataSet) {
    // Clear previous tables if any
    $('#manual-data-table').empty();
    $('#file-tbl').hide(); // Hide file table by default
    $('#mnl-tbl').hide(); // Hide manual table by default

    if (fileDataSet) {
        displayDataSetInTable(fileDataSet, '#file-data-table');
        $('#file-tbl').show(); // Show file table
        // $('#mnl-tbl').empty(); // empty manual table
        $('#manual-data-table').hide();
        $('#file-data-table').show();

    } 

    if (manualDataSet) {
        displayDataSetInTable(manualDataSet, '#manual-data-table');
        $('#mnl-tbl').show(); // Show manual table
        // $('#file-tbl').empty(); // empty file table
        $('#file-data-table').hide();
        $('#manual-data-table').show();
    }
        // Show the table section after updating tables
        $('#tbl-section').show();    
}

function displayDataSetInTable(dataSet, tableId) {
    if (!dataSet || !dataSet.data || dataSet.data.length === 0) {
        console.error("Error: DataSet is undefined or empty");
        $(tableId).empty(); // Clear the table if data is empty
        return;
    }
    // Create the table container
    let tableContainer = $('<div>');
        // Create the heading
    let heading = $('<h3>').text(dataSet.choosen[0]);

    // Append the heading to the table container
    tableContainer.append(heading);
    
    const table = $('<table>').addClass('data-table');
    const tableCaption = $('<caption>').text(dataSet.choosen[0]); // Displaying the value of "choosen" as caption
    table.append(tableCaption);

    // Create table headers
    const keys = Object.keys(dataSet);
    const headersRow = $('<tr>');

    // Add Action header to the first cell
    headersRow.append(createDropdown());

    // Add other headers
    keys.forEach(key => {
        if (key !== 'choosen') {
            headersRow.append($('<th>').text(key));
        }
    });
    table.append(headersRow);

    // Create table rows
    for (let i = 0; i < dataSet.data.length; i++) {
        const dataRow = $('<tr>');

        // Add dropdown cell only to the first cell of the first column
        if (i >= 0) {
            // For other rows, add checkboxes in the first column
            const checkboxCell = $('<td>').append(
                $('<input>').attr('type', 'checkbox').addClass('row-checkbox')
            );
            dataRow.append(checkboxCell);
        }

        // Add cells for other columns
        keys.forEach(key => {
            if (key !== 'choosen') {
                const cellData = dataSet[key][i];
                dataRow.append($('<td>').text(cellData));
            }
        });
        table.append(dataRow);
    }
    // Append the table to the table container
    tableContainer.append(table);
    
    // Append the table to the specified container
    $(tableId).empty().append(table); // Empty the table container before appending
}
// *************************************************************************************************************************
// ************************************   Dropdown Based dataSet preperation Start  *********************************************
// *************************************************************************************************************************

// Function to create the dropdown
function createDropdown() {
    const dropdownHeader = $('<th>').text('Action'); // Create a header cell for the dropdown
    const dropdown = $('<select>').append(
        $('<option>').text('select'),
        $('<option>').text('First 50').attr('value', 'Option 1'),
        $('<option>').text('First 100').attr('value', 'Option 2'),
        $('<option>').text('First 150').attr('value', 'Option 3'),
        $('<option>').text('More').attr('value', 'Choose').prop('disabled', true)
    );

    dropdownHeader.append(dropdown); // Append the dropdown to the header cell
    return dropdownHeader; // Return the dropdown header cell
}
    // Dropdown change event handler
    $(document).on("change", "select", function() {
        var selection = $(this).val();
        handleCheckboxSelection(selection);
    });

    // Check_all checkbox click event handler
    $(document).on("click", "#check_all", function() {
        if ($(this).prop("checked")) {
            $("input:checkbox.row-checkbox").prop("checked", true);
        } else {
            $("input:checkbox.row-checkbox").prop("checked", false);
        }
    });

// Checkbox change event handler
$(document).on("change", "input:checkbox.row-checkbox", function() {
    var selectedValue = $("select").val(); // Get the current dropdown selection
    var totalChecked = $("input:checkbox.row-checkbox:checked").length; // Get the total checked checkboxes

    // Check if the selected checkboxes exceed the limit
    if (totalChecked > 150) {
        $(this).prop("checked", false); // Uncheck the current checkbox if the limit is exceeded
        return; // Exit the function to prevent further processing
    }

    updateCheckAllCheckbox();
    handleCheckboxSelection(selectedValue); // Apply limit after checkbox status changes
});

// Function to handle checkbox selection based on dropdown selection
function handleCheckboxSelection(selection) {
    // Enable all checkboxes and remove disabled attribute
    $("input:checkbox.row-checkbox").prop("disabled", false);

    // Uncheck all checkboxes if the first option is selected
    if (selection === "select") {
        $("input:checkbox.row-checkbox").prop("checked", false);
    }

    // Check checkboxes based on selection, limiting to 150 checkboxes
    if (selection === "Option 1") { // First 50
        checkLimitedCheckboxes(50);
    } else if (selection === "Option 2") { // First 100
        checkLimitedCheckboxes(100);
    } else if (selection === "Option 3") { // First 150
        checkLimitedCheckboxes(150);
    }

    // Update check_all checkbox based on checked checkboxes
    updateCheckAllCheckbox();

    // Store checked checkbox values in the dataset
    storeCheckedValues();
}

// Function to check a limited number of checkboxes
function checkLimitedCheckboxes(limit) {
    var $checkboxes = $("input:checkbox.row-checkbox");
    $checkboxes.prop("checked", false); // Uncheck all checkboxes first
    $checkboxes.slice(0, limit).prop("checked", true); // Check only up to the specified limit

    // Disable remaining checkboxes if the limit is reached
    if ($checkboxes.length > limit) {
        $checkboxes.slice(limit).prop("disabled", true);
    }
}

// Checkbox change event handler
$("input:checkbox.row-checkbox").on("change", function() {
    updateCheckAllCheckbox();
    handleCheckboxSelection($("select").val()); // Apply limit after checkbox status changes
});

// Function to update the check_all checkbox based on checked checkboxes
function updateCheckAllCheckbox() {
    var total_check_boxes = $("input:checkbox.row-checkbox").length;
    var total_checked_boxes = $("input:checkbox.row-checkbox:checked").length;

    // If all checkboxes are checked, check the check_all checkbox
    $("#check_all").prop("checked", total_check_boxes === total_checked_boxes);
}

// Function to store checked checkbox values in the dataset
function storeCheckedValues() {
    // Initialize clientUrlSet object
    var clientUrlSet = {
        url_list: [],
        column_number: [],
        row_number: [],
        sheet_number: [],
        choosen: []
    };
    // Retrieve the caption value once
    var captionText = $("caption").text();
    // Iterate through checked checkboxes and store values
    $("input:checkbox.row-checkbox:checked").each(function() {
        var $row = $(this).closest("tr");
        clientUrlSet.url_list.push($row.find("td:nth-child(2)").text());
        clientUrlSet.column_number.push($row.find("td:nth-child(3)").text());
        clientUrlSet.row_number.push($row.find("td:nth-child(4)").text());
        clientUrlSet.sheet_number.push($row.find("td:nth-child(5)").text());

    });
    // Push the caption value to the choosen array once
    clientUrlSet.choosen.push(captionText);

    // Check if data is empty
    if (clientUrlSet.url_list.length === 0) {
        console.error("Error: No data found");
        return null; // Return null if no data is found
    }
    // Bind click event to send data to server
    $("#send_serve").off("click").on("click", function() {
        sendDataToServer(clientUrlSet);
        // Output the dataset for verification
        console.log("Before Sending to server:",clientUrlSet);
});
}
// Function to send data to the server
async function sendDataToServer(clientUrlSet) {
    // Record start time
    var startTime = new Date().getTime();

    // Display loading indicator
    $('#loadingIndicator').show();

    // Make sure dataSet is not empty
    if (!clientUrlSet || !clientUrlSet.url_list || clientUrlSet.url_list.length === 0) {
        console.error("Error: DataSet is undefined or empty");
        return;
    } else {
        console.log("Before Sending to server:",clientUrlSet);
        console.log("Stringified Data:", JSON.stringify(clientUrlSet)); // Log the stringified data
        try {
            // Perform an asynchronous AJAX POST request to the server endpoint
            const response = await $.ajax({
                url: "/process_url_data",
                type: "POST",
                contentType: "application/json",
                data: JSON.stringify(clientUrlSet)
            });

            // Calculate processing time
            var endTime = new Date().getTime();
            var processingTime = endTime - startTime;

            // Format processing time
            var formattedTime;
            if (processingTime < 1000) {
                formattedTime = processingTime + " milliseconds";
            } else if (processingTime < 60000) {
                formattedTime = (processingTime / 1000).toFixed(2) + " seconds";
            } else {
                formattedTime = (processingTime / 60000).toFixed(2) + " minutes";
            }
            console.log("Processing time:", formattedTime);

            if (response.error) {
                console.error("Error from server:", response.error);
                // Handle the specific error message here
            } else {
                console.log("Data sent successfully:", response);
                // Process the successful response data here
            }
        } catch (error) {
            console.error("Error sending data to server:", error);
            // Handle the error here if needed
        } finally {
            // Hide loading indicator after request completes
            $('#loadingIndicator').hide();
        }
    }
}


// *************************************************************************************************************************
// ************************************   Dropdown Based dataSet preperation Ended  *********************************************
// *************************************************************************************************************************


// Global variable to store the selected sheet
let selectedSheet;

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
            selectedSheet = data.selected_sheet; // Update the selected sheet based on the server's response
            if (!data.is_csv) {
                populateSheetDropdown(selectedSheet, data.sheet_names); // Populate sheet dropdown for XLSX files
                populateColumnDropdown(data.sheet_columns[selectedSheet], selectedSheet, data.column_data); // Populate column dropdown for the selected sheet
                $('#sheet-name').val(selectedSheet); // Update the selected sheet without resetting
                $('#sheet-name').show(); // Show sheet dropdown for XLSX files
                $('label[for="sheet-name"]').show(); // Show label for XLSX files
            } else {
                populateColumnDropdown(data.sheet_columns, selectedSheet, data.column_data); // Populate column dropdown for CSV files
                $('#sheet-name').empty().hide(); // Hide sheet dropdown for CSV files
                $('label[for="sheet-name"]').hide(); // Hide label for CSV files
            }
            // Fetch column data for the default selected column
            var selectedColumn = $('#column-name').val(); // Get the selected column
            if (selectedColumn) {
                var formData = new FormData(); // Initialize FormData object
                formData.append('file', $('#file')[0].files[0]); // Include the file data
                formData.append('selected_sheet', selectedSheet); // Pass the selected sheet
                formData.append('selected_column', selectedColumn); // Pass the selected column
                fetchColumnURLs(formData); // Pass the FormData object to fetch column Data
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
        var formData = new FormData(); // Initialize FormData object
        formData.append('file', $('#file')[0].files[0]); // Include the file data
        formData.append('selected_sheet', selectedSheet); // Pass the selected sheet
        formData.append('selected_column', selectedColumn); // Pass the selected column
        fetchColumnURLs(formData); // Pass the FormData object to fetch column Data
    }
}

// Handle column dropdown change event
$(document).on('change', '#column-name', function () {
    var selectedColumn = $(this).val(); // Get the selected column
    if (selectedColumn) {
        selectedSheet= $('#sheet-name').val();
        var formData = new FormData(); // Initialize FormData object
        formData.append('file', $('#file')[0].files[0]); // Include the file data
        formData.append('selected_sheet', selectedSheet); // Pass the selected sheet
        formData.append('selected_column', selectedColumn); // Pass the selected column
        fetchColumnURLs(formData); // Pass the FormData object to fetch column Data
    } else {
        console.log('No valid column selected.');
    }
});

// Function to handle sheet dropdown change event
$(document).on('change', '#sheet-name', function () {
    selectedSheet = $(this).val(); // Update the selected sheet value
    var formData = new FormData(); // Construct FormData object with selected sheet value
    formData.append('file', $('#file')[0].files[0]); // Include the file data
    formData.append('selected_sheet', selectedSheet); // Use the first sheet if selectedSheet is null
    fetchSheetAndColumnNames(formData); // Pass the FormData object to fetch sheet and column names
});

// Function to handle file change event
$(document).on('change', '#file', function () {
    $('#valid_list').empty(); // Clear the valid_list div
    var fileInput = $(this)[0].files[0]; // Get the selected file
    var formData = new FormData(); // Initialize FormData object
    if (fileInput) {
        formData.append('file', fileInput); // Include the file data
        fetchSheetAndColumnNames(formData); // Pass the FormData object to fetch sheet and column names
    } else {
        console.error('No file selected.');
        $('#tbl-section').hide();
        $('#url-container').hide();
        $('#sheet-name').empty();
        $('#column-name').empty();
    }
});

});
