// DICOM Viewer JS - Handles DICOM display and interaction
document.addEventListener('DOMContentLoaded', function () {
    // Get elements
    const dicomImage = document.getElementById('dicom-image');
    const windowWidthSlider = document.getElementById('window-width');
    const windowCenterSlider = document.getElementById('window-center');
    const zoomSlider = document.getElementById('zoom-level');
    const presetButtons = document.querySelectorAll('.preset-button');

    // Initialize variables
    let originalPixelData = null;
    let imageWidth = 0;
    let imageHeight = 0;
    let windowWidth = windowWidthSlider ? parseInt(windowWidthSlider.value) : 255;
    let windowCenter = windowCenterSlider ? parseInt(windowCenterSlider.value) : 127;
    let zoomLevel = zoomSlider ? parseFloat(zoomSlider.value) : 1.0;

    // Apply initial window/level values
    function applyWindowLevel() {
        if (!dicomImage) return;

        // If sliders are not present, don't do anything
        if (!windowWidthSlider || !windowCenterSlider) return;

        // Update zoom if slider exists
        if (zoomSlider) {
            dicomImage.style.transform = `scale(${zoomLevel})`;
        }

        // For actual DICOM pixel manipulation, you would apply windowing here
        // In this simplified version, we just apply CSS filters
        const brightness = ((windowCenter - 127) / 255) * 100;
        const contrast = (windowWidth / 255) * 200;

        dicomImage.style.filter = `brightness(${100 + brightness}%) contrast(${contrast}%)`;
    }

    // Event listeners for window/level sliders
    if (windowWidthSlider) {
        windowWidthSlider.addEventListener('input', function () {
            windowWidth = parseInt(this.value);
            document.getElementById('width-value').textContent = windowWidth;
            applyWindowLevel();
        });
    }

    if (windowCenterSlider) {
        windowCenterSlider.addEventListener('input', function () {
            windowCenter = parseInt(this.value);
            document.getElementById('center-value').textContent = windowCenter;
            applyWindowLevel();
        });
    }

    if (zoomSlider) {
        zoomSlider.addEventListener('input', function () {
            zoomLevel = parseFloat(this.value);
            document.getElementById('zoom-value').textContent = zoomLevel.toFixed(1) + 'x';
            applyWindowLevel();
        });
    }

    // Preset buttons
    if (presetButtons) {
        presetButtons.forEach(button => {
            button.addEventListener('click', function () {
                const preset = this.dataset.preset;

                // Remove active class from all buttons
                presetButtons.forEach(btn => btn.classList.remove('bg-pink-600', 'text-white'));

                // Add active class to clicked button
                this.classList.add('bg-pink-600', 'text-white');

                // Apply preset
                switch (preset) {
                    case 'default':
                        windowWidth = 255;
                        windowCenter = 127;
                        break;
                    case 'bone':
                        windowWidth = 1800;
                        windowCenter = 400;
                        break;
                    case 'breast':
                        windowWidth = 1500;
                        windowCenter = 500;
                        break;
                    case 'lung':
                        windowWidth = 1500;
                        windowCenter = -600;
                        break;
                    case 'brain':
                        windowWidth = 80;
                        windowCenter = 40;
                        break;
                }

                // Update sliders
                if (windowWidthSlider) {
                    windowWidthSlider.value = windowWidth;
                    document.getElementById('width-value').textContent = windowWidth;
                }

                if (windowCenterSlider) {
                    windowCenterSlider.value = windowCenter;
                    document.getElementById('center-value').textContent = windowCenter;
                }

                applyWindowLevel();
            });
        });
    }

    // Apply initial settings
    applyWindowLevel();

    // Check for the file input on the index page
    const fileInput = document.getElementById('file-input');
    const previewButton = document.getElementById('preview-dicom-button');

    if (fileInput) {
        fileInput.addEventListener('change', function (e) {
            const file = e.target.files[0];
            if (file && file.name.toLowerCase().endsWith('.dcm')) {
                // Show the DICOM preview button
                if (previewButton) {
                    previewButton.classList.remove('hidden');

                    // Set the onclick to submit to the preview endpoint
                    previewButton.onclick = function () {
                        const formData = new FormData();
                        formData.append('file', file);

                        // Save file and redirect to preview
                        fetch('/upload_for_preview', {
                            method: 'POST',
                            body: formData
                        })
                            .then(response => response.json())
                            .then(data => {
                                if (data.success) {
                                    window.location.href = '/dicom_preview?file=' + data.path;
                                } else {
                                    alert('Error uploading DICOM file: ' + data.error);
                                }
                            })
                            .catch(error => {
                                console.error('Error:', error);
                                alert('Error uploading DICOM file');
                            });
                    };
                }
            } else if (previewButton) {
                // Hide preview button for non-DICOM files
                previewButton.classList.add('hidden');
            }
        });
    }
}); 