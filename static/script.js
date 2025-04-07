document.addEventListener('DOMContentLoaded', () => {
    const dropArea = document.getElementById('drop-area');
    const fileElem = document.getElementById('fileElem');
    const loadingIndicator = document.getElementById('loading-indicator');
    const resultsSection = document.getElementById('results-section');
    const uploadSection = document.getElementById('upload-section');
    const imagePreview = document.getElementById('image-preview');
    const predictionResult = document.getElementById('prediction-result');
    const confidenceScore = document.getElementById('confidence-score');
    const gradCamContainer = document.getElementById('grad-cam-container');
    const gradCamImage = document.getElementById('grad-cam-image');
    const errorMessage = document.getElementById('error-message');
    const errorText = document.getElementById('error-text');
    const uploadNewBtn = document.getElementById('upload-new-btn');
    const downloadReportBtn = document.getElementById('download-report-btn');

    let currentResultData = null; // Store result data for report generation

    // Prevent default drag behaviors
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropArea.addEventListener(eventName, preventDefaults, false);
        document.body.addEventListener(eventName, preventDefaults, false); // Prevent dropping elsewhere
    });

    // Highlight drop area when item is dragged over it
    ['dragenter', 'dragover'].forEach(eventName => {
        dropArea.addEventListener(eventName, highlight, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropArea.addEventListener(eventName, unhighlight, false);
    });

    // Handle dropped files
    dropArea.addEventListener('drop', handleDrop, false);

    // Handle file selection via button
    fileElem.addEventListener('change', handleFileSelect, false);

    // Handle "Upload Another" button
    uploadNewBtn.addEventListener('click', resetUI, false);

    // Handle "Download Report" button
    downloadReportBtn.addEventListener('click', handleDownloadReport, false);


    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    function highlight(e) {
        dropArea.classList.add('highlight');
    }

    function unhighlight(e) {
        dropArea.classList.remove('highlight');
    }

    function handleDrop(e) {
        const dt = e.dataTransfer;
        const files = dt.files;
        handleFiles(files);
    }

    function handleFileSelect(e) {
        handleFiles(e.target.files);
         // Reset file input to allow uploading the same file again
        e.target.value = null;
    }

    function handleFiles(files) {
        if (files.length > 1) {
            showError("Please upload only one file at a time.");
            return;
        }
        const file = files[0];
        // Basic validation (can add more checks like size, type)
        if (!file.type.startsWith('image/')) {
            showError("Invalid file type. Please upload an image (PNG, JPG, BMP, GIF).");
            return;
        }
        // Max size check (e.g., 16MB)
        if (file.size > 16 * 1024 * 1024) {
             showError("File size exceeds the 16MB limit.");
             return;
        }

        uploadFile(file);
    }

    function uploadFile(file) {
        // Hide previous results/errors and show loading
        hideError();
        resultsSection.classList.add('hidden');
        uploadSection.classList.add('hidden'); // Hide upload section too
        loadingIndicator.classList.remove('hidden');
        downloadReportBtn.disabled = true; // Disable report button during loading
        currentResultData = null; // Clear previous results

        const formData = new FormData();
        formData.append('file', file);

        fetch('/predict', {
            method: 'POST',
            body: formData,
        })
        .then(response => {
            if (!response.ok) {
                // Try to parse error message from server JSON response
                return response.json().then(err => {
                    throw new Error(err.error || `Server error: ${response.statusText}`);
                });
            }
            return response.json();
        })
        .then(data => {
            loadingIndicator.classList.add('hidden');
            if (data.error) {
                showError(data.error);
                 uploadSection.classList.remove('hidden'); // Show upload section again on error
            } else {
                displayResults(data);
                resultsSection.classList.remove('hidden');
                downloadReportBtn.disabled = false; // Enable report button
                currentResultData = data; // Store data for report
            }
        })
        .catch(error => {
            console.error('Upload error:', error);
            loadingIndicator.classList.add('hidden');
            showError(error.message || 'An unexpected error occurred during upload.');
            uploadSection.classList.remove('hidden'); // Show upload section again on error
        });
    }

    function displayResults(data) {
        imagePreview.src = data.preview_src || '#';
        predictionResult.textContent = data.prediction || '--';
        confidenceScore.textContent = data.confidence || '--';

        if (data.grad_cam_src) {
            gradCamImage.src = data.grad_cam_src;
            gradCamContainer.classList.remove('hidden');
        } else {
            gradCamContainer.classList.add('hidden');
        }
    }

    function resetUI() {
        resultsSection.classList.add('hidden');
        uploadSection.classList.remove('hidden');
        loadingIndicator.classList.add('hidden');
        hideError();
        // Clear file input visually if needed (though change event handles re-upload)
        fileElem.value = '';
        // Reset result fields (optional, happens on next successful upload)
        imagePreview.src = '#';
        predictionResult.textContent = '--';
        confidenceScore.textContent = '--';
        gradCamContainer.classList.add('hidden');
        downloadReportBtn.disabled = true;
        currentResultData = null;
    }

    function showError(message) {
        errorText.textContent = message;
        errorMessage.classList.remove('hidden');
        // Optional: Auto-hide error after some time
        // setTimeout(hideError, 7000);
    }

    function hideError() {
        errorMessage.classList.add('hidden');
        errorText.textContent = '';
    }

     function handleDownloadReport() {
        if (!currentResultData) {
            showError("No result data available to generate report.");
            return;
        }

        downloadReportBtn.disabled = true; // Prevent multiple clicks
        downloadReportBtn.innerHTML = `
            <svg class="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            Generating...`;


        fetch('/generate_report', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(currentResultData), // Send result data to backend
        })
        .then(response => {
            if (!response.ok) {
                 // Try to get error details from response body
                 return response.text().then(text => {
                    try {
                        const err = JSON.parse(text);
                        throw new Error(err.error || `Failed to generate report: ${response.statusText}`);
                    } catch (e) {
                        // If response is not JSON or doesn't have 'error' key
                        throw new Error(`Failed to generate report: ${response.statusText} - ${text}`);
                    }
                });
            }
            return response.blob(); // Get the PDF blob
        })
        .then(blob => {
            // Create a link to download the PDF
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.style.display = 'none';
            a.href = url;
            // Extract filename or use default
            const filename = currentResultData.filename ? `mammogram_report_${currentResultData.filename.split('.')[0]}.pdf` : 'mammogram_report.pdf';
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);

            // Reset button state
            downloadReportBtn.disabled = false;
            downloadReportBtn.innerHTML = `<i data-lucide="download" class="w-5 h-5 mr-2"></i>Download Report (PDF)`;
            // Re-initialize Lucide icons if necessary after changing innerHTML
            if (window.lucide) {
                 window.lucide.createIcons();
            }


        })
        .catch(error => {
            console.error('Report generation error:', error);
            showError(error.message || 'Failed to generate PDF report.');
             // Reset button state on error
            downloadReportBtn.disabled = false;
            downloadReportBtn.innerHTML = `<i data-lucide="download" class="w-5 h-5 mr-2"></i>Download Report (PDF)`;
             if (window.lucide) {
                 window.lucide.createIcons();
            }
        });
    }

    // Initialize Lucide icons on load
    if (window.lucide) {
        window.lucide.createIcons();
    } else {
        console.warn("Lucide icons script not loaded yet.");
        // Optionally wait for it if needed, though DOMContentLoaded should suffice
    }
});
