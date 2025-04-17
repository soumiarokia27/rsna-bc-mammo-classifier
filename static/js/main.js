/**
 * MammoSense - Main JavaScript File
 * Contains all client-side functionality for the application
 */

document.addEventListener('DOMContentLoaded', function () {
    // Initialize all components
    initAccessibility();
    initDarkModeToggle();
    initKeyboardFocus();
    initImageZoom();
    initMobileMenu();
    initScrollEffects();
    initFileUpload();

    // Add keyboard detection
    window.addEventListener('keydown', function (e) {
        document.body.classList.add('keyboard-user');
    });

    window.addEventListener('mousedown', function (e) {
        document.body.classList.remove('keyboard-user');
    });
});

/**
 * Initialize accessibility features
 */
function initAccessibility() {
    // Add ARIA attributes where needed
    const uploadContainers = document.querySelectorAll('.upload-container');
    uploadContainers.forEach(container => {
        container.setAttribute('role', 'button');
        container.setAttribute('aria-label', 'Upload a mammogram image');
        container.setAttribute('tabindex', '0');

        // Allow keyboard activation
        container.addEventListener('keydown', function (e) {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                container.click();
            }
        });
    });

    // Make tooltips accessible
    const tooltips = document.querySelectorAll('[data-tooltip]');
    tooltips.forEach(element => {
        element.setAttribute('role', 'tooltip');
        element.setAttribute('tabindex', '0');
    });
}

/**
 * Initialize dark mode toggle functionality
 */
function initDarkModeToggle() {
    // Create the dark mode toggle button if it doesn't exist
    if (!document.querySelector('.dark-mode-toggle')) {
        const toggle = document.createElement('button');
        toggle.className = 'dark-mode-toggle';
        toggle.innerHTML = '<i class="fas fa-moon text-primary-600"></i>';
        toggle.setAttribute('aria-label', 'Toggle dark mode');
        toggle.setAttribute('data-tooltip', 'Toggle dark/light mode');
        document.body.appendChild(toggle);

        // Check for saved preference
        const darkMode = localStorage.getItem('darkMode');
        if (darkMode === 'true') {
            document.body.classList.add('dark-mode');
            toggle.innerHTML = '<i class="fas fa-sun text-yellow-400"></i>';
        } else {
            document.body.classList.remove('dark-mode');
            toggle.innerHTML = '<i class="fas fa-moon text-primary-600"></i>';
        }

        // Toggle dark mode on click
        toggle.addEventListener('click', function () {
            document.body.classList.toggle('dark-mode');
            const isDarkMode = document.body.classList.contains('dark-mode');
            localStorage.setItem('darkMode', isDarkMode);

            // Update icon with appropriate color
            if (isDarkMode) {
                toggle.innerHTML = '<i class="fas fa-sun text-yellow-400"></i>';
            } else {
                toggle.innerHTML = '<i class="fas fa-moon text-primary-600"></i>';
            }

            // Add a subtle animation effect
            toggle.classList.add('animate-pulse');
            setTimeout(() => {
                toggle.classList.remove('animate-pulse');
            }, 500);
        });
    }
}

/**
 * Initialize keyboard focus detection
 */
function initKeyboardFocus() {
    // Detect keyboard navigation vs mouse navigation
    document.body.addEventListener('mousedown', function () {
        document.body.classList.remove('keyboard-user');
    });

    document.body.addEventListener('keydown', function (e) {
        if (e.key === 'Tab') {
            document.body.classList.add('keyboard-user');
        }
    });
}

/**
 * Initialize image zoom functionality for mammogram images
 */
function initImageZoom() {
    const images = document.querySelectorAll('.aspect-square img, .dicom-image');

    images.forEach(img => {
        img.addEventListener('click', function () {
            // Create modal for image zoom
            const modal = document.createElement('div');
            modal.className = 'fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50';
            modal.setAttribute('role', 'dialog');
            modal.setAttribute('aria-modal', 'true');

            // Create image container
            const imgContainer = document.createElement('div');
            imgContainer.className = 'relative max-w-3xl max-h-full p-4';

            // Create close button
            const closeBtn = document.createElement('button');
            closeBtn.className = 'absolute top-0 right-0 -mt-10 -mr-10 bg-white rounded-full p-2 text-gray-800 hover:text-primary-500';
            closeBtn.innerHTML = '<i class="fas fa-times"></i>';
            closeBtn.setAttribute('aria-label', 'Close zoom view');

            // Create zoomed image
            const zoomedImg = document.createElement('img');
            zoomedImg.src = this.src;
            zoomedImg.className = 'max-w-full max-h-[80vh] object-contain';
            zoomedImg.setAttribute('alt', this.alt || 'Mammogram image zoom view');

            // Add elements to DOM
            imgContainer.appendChild(zoomedImg);
            imgContainer.appendChild(closeBtn);
            modal.appendChild(imgContainer);
            document.body.appendChild(modal);

            // Handle close
            closeBtn.addEventListener('click', function () {
                document.body.removeChild(modal);
            });

            modal.addEventListener('click', function (e) {
                if (e.target === modal) {
                    document.body.removeChild(modal);
                }
            });

            // Handle escape key
            document.addEventListener('keydown', function escHandler(e) {
                if (e.key === 'Escape') {
                    document.body.removeChild(modal);
                    document.removeEventListener('keydown', escHandler);
                }
            });
        });

        // Add indicator that image is zoomable
        img.style.cursor = 'zoom-in';
        const parent = img.closest('.aspect-square, .dicom-image-wrapper');
        if (parent) {
            parent.setAttribute('data-tooltip', 'Click to zoom');
        }
    });
}

/**
 * Initialize mobile menu functionality
 */
function initMobileMenu() {
    const mobileMenuButton = document.querySelector('.mobile-menu-button');
    const mobileMenu = document.querySelector('.mobile-menu');

    if (mobileMenuButton && mobileMenu) {
        mobileMenuButton.addEventListener('click', function () {
            const expanded = mobileMenuButton.getAttribute('aria-expanded') === 'true';
            mobileMenuButton.setAttribute('aria-expanded', !expanded);
            mobileMenu.classList.toggle('hidden');
        });
    }
}

/**
 * Initialize scroll effects
 */
function initScrollEffects() {
    // Smooth scroll for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            const targetId = this.getAttribute('href');
            if (targetId !== '#') {
                e.preventDefault();

                const targetElement = document.querySelector(targetId);
                if (targetElement) {
                    window.scrollTo({
                        top: targetElement.offsetTop - 20,
                        behavior: 'smooth'
                    });

                    // Set focus to the target for accessibility
                    targetElement.setAttribute('tabindex', '-1');
                    targetElement.focus();
                }
            }
        });
    });

    // Add scroll-triggered animations
    const animateElements = document.querySelectorAll('.animate-on-scroll');

    if ('IntersectionObserver' in window) {
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('is-visible');
                    observer.unobserve(entry.target);
                }
            });
        }, { threshold: 0.1 });

        animateElements.forEach(el => {
            observer.observe(el);
        });
    } else {
        // Fallback for browsers without IntersectionObserver
        animateElements.forEach(el => {
            el.classList.add('is-visible');
        });
    }
}

/**
 * Initialize file upload functionality
 */
function initFileUpload() {
    const fileInput = document.getElementById('file-input');
    const uploadForm = document.getElementById('upload-form');
    const uploadContainer = document.querySelector('.upload-container');
    const dropZone = document.querySelector('.drop-zone');
    const filePreview = document.querySelector('.file-preview');
    const previewImage = document.querySelector('.preview-image');
    const previewName = document.querySelector('.preview-name');
    const previewSize = document.querySelector('.preview-size');
    const previewType = document.querySelector('.preview-type');
    const previewInfo = document.querySelector('.preview-info');
    const removeButton = document.querySelector('.remove-file');
    const submitButton = document.getElementById('analyze-button');
    const dicomPreviewButton = document.getElementById('preview-dicom-button');

    if (!fileInput) return;

    // Handle file input change
    fileInput.addEventListener('change', function (e) {
        handleFileSelection(e.target.files[0]);
    });

    // Handle drag and drop
    if (dropZone) {
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            dropZone.addEventListener(eventName, preventDefaults, false);
        });

        function preventDefaults(e) {
            e.preventDefault();
            e.stopPropagation();
        }

        ['dragenter', 'dragover'].forEach(eventName => {
            dropZone.addEventListener(eventName, highlight, false);
        });

        ['dragleave', 'drop'].forEach(eventName => {
            dropZone.addEventListener(eventName, unhighlight, false);
        });

        function highlight() {
            dropZone.classList.add('border-primary-500', 'border-dashed');
        }

        function unhighlight() {
            dropZone.classList.remove('border-primary-500', 'border-dashed');
        }

        dropZone.addEventListener('drop', function (e) {
            const dt = e.dataTransfer;
            const file = dt.files[0];

            if (file) {
                fileInput.files = dt.files;
                handleFileSelection(file);
            }
        });
    }

    // Function to handle file selection
    function handleFileSelection(file) {
        if (!file) return;

        // Check if file is valid
        const validTypes = ['image/jpeg', 'image/png', 'application/dicom'];
        const isValidType = validTypes.includes(file.type) || file.name.toLowerCase().endsWith('.dcm');

        if (!isValidType) {
            alert('Please select a valid image file (JPEG, PNG) or DICOM file.');
            fileInput.value = '';
            return;
        }

        // Enable submit button
        if (submitButton) {
            submitButton.disabled = false;
            submitButton.classList.remove('opacity-50', 'cursor-not-allowed');
            submitButton.classList.add('hover:bg-primary-700');
        }

        // Show DICOM preview button for DICOM files
        if (dicomPreviewButton) {
            if (file.name.toLowerCase().endsWith('.dcm')) {
                dicomPreviewButton.classList.remove('hidden');
            } else {
                dicomPreviewButton.classList.add('hidden');
            }
        }

        // Update file preview
        if (filePreview) {
            filePreview.classList.remove('hidden');
        }

        if (uploadContainer) {
            uploadContainer.classList.add('border-primary-500');
        }

        if (previewImage) {
            if (!file.name.toLowerCase().endsWith('.dcm')) {
                const reader = new FileReader();
                reader.onload = function (e) {
                    previewImage.src = e.target.result;
                    previewImage.classList.remove('hidden');
                };
                reader.readAsDataURL(file);
            } else {
                // For DICOM files, show a placeholder
                previewImage.src = '/static/images/dicom-placeholder.svg';
                previewImage.classList.remove('hidden');

                // Add DICOM badge to preview
                const dicomBadge = document.createElement('div');
                dicomBadge.className = 'absolute top-2 right-2 bg-primary-600 text-white text-xs px-2 py-1 rounded-full';
                dicomBadge.textContent = 'DICOM';
                previewImage.parentElement.appendChild(dicomBadge);
            }
        }

        if (previewName) {
            previewName.textContent = file.name;
        }

        if (previewSize) {
            previewSize.textContent = formatFileSize(file.size);
        }

        if (previewType) {
            previewType.textContent = file.name.toLowerCase().endsWith('.dcm') ? 'DICOM' : file.type.split('/')[1].toUpperCase();
        }

        if (previewInfo) {
            previewInfo.classList.remove('hidden');

            // Add specific info for DICOM files
            if (file.name.toLowerCase().endsWith('.dcm')) {
                const dicomNote = document.createElement('div');
                dicomNote.className = 'text-primary-600 text-sm mt-2';
                dicomNote.innerHTML = '<i class="fas fa-info-circle mr-1"></i> DICOM preview will be available after upload';
                previewInfo.appendChild(dicomNote);
            }
        }

        // Enable remove button
        if (removeButton) {
            removeButton.classList.remove('hidden');
            removeButton.addEventListener('click', function () {
                fileInput.value = '';
                filePreview.classList.add('hidden');
                previewImage.classList.add('hidden');
                previewInfo.classList.add('hidden');
                removeButton.classList.add('hidden');
                uploadContainer.classList.remove('border-primary-500');

                // Remove any DICOM badges
                const dicomBadge = previewImage.parentElement.querySelector('.bg-primary-600');
                if (dicomBadge) {
                    dicomBadge.remove();
                }

                // Remove DICOM info notes
                const dicomNote = previewInfo.querySelector('.text-primary-600');
                if (dicomNote) {
                    dicomNote.remove();
                }

                // Disable submit button
                if (submitButton) {
                    submitButton.disabled = true;
                    submitButton.classList.add('opacity-50', 'cursor-not-allowed');
                    submitButton.classList.remove('hover:bg-primary-700');
                }

                // Hide DICOM preview button
                if (dicomPreviewButton) {
                    dicomPreviewButton.classList.add('hidden');
                }
            });
        }
    }

    // Format file size
    function formatFileSize(bytes) {
        if (bytes < 1024) return bytes + ' bytes';
        else if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB';
        else return (bytes / 1048576).toFixed(1) + ' MB';
    }
} 