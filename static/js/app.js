// app.js - Main JavaScript file for the Smart File Storage application

document.addEventListener('DOMContentLoaded', function() {
    // Initialize dropdowns
    initializeDropdowns();
    
    // Initialize theme toggle
    initializeThemeToggle();
    
    // Initialize file upload
    initializeFileUpload();
    
    // Initialize search
    initializeSearch();
    
    // Initialize tooltips
    initializeTooltips();
    
    // Add event listeners for file cards
    initializeFileCards();
});

/**
 * Initialize bootstrap dropdowns
 */
function initializeDropdowns() {
    const dropdownElementList = [].slice.call(document.querySelectorAll('.dropdown-toggle'));
    dropdownElementList.map(function(dropdownToggleEl) {
        return new bootstrap.Dropdown(dropdownToggleEl);
    });
}

/**
 * Initialize theme toggle functionality
 */
function initializeThemeToggle() {
    const themeToggle = document.getElementById('theme-toggle');
    
    if (themeToggle) {
        themeToggle.addEventListener('click', function() {
            const currentTheme = document.documentElement.getAttribute('data-bs-theme');
            const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
            
            document.documentElement.setAttribute('data-bs-theme', newTheme);
            
            // Save theme preference
            const form = document.createElement('form');
            form.method = 'POST';
            form.action = '/toggle-theme';
            
            const input = document.createElement('input');
            input.type = 'hidden';
            input.name = 'theme';
            input.value = newTheme;
            
            form.appendChild(input);
            document.body.appendChild(form);
            form.submit();
        });
    }
}

/**
 * Initialize file upload functionality with progress indicator
 */
function initializeFileUpload() {
    const fileInput = document.getElementById('file-upload-input');
    const uploadForm = document.getElementById('upload-form');
    const uploadBtn = document.getElementById('upload-btn');
    const uploadProgress = document.getElementById('upload-progress');
    
    if (fileInput && uploadForm) {
        fileInput.addEventListener('change', function() {
            if (fileInput.files.length > 0) {
                const fileName = fileInput.files[0].name;
                const fileSize = formatFileSize(fileInput.files[0].size);
                
                document.getElementById('selected-file-name').textContent = fileName;
                document.getElementById('selected-file-size').textContent = fileSize;
                document.getElementById('file-selection-info').classList.remove('d-none');
                
                // Enable upload button
                if (uploadBtn) {
                    uploadBtn.disabled = false;
                }
            }
        });
        
        uploadForm.addEventListener('submit', function() {
            // Show progress
            if (uploadProgress) {
                uploadProgress.classList.remove('d-none');
            }
            
            // Disable button during upload
            if (uploadBtn) {
                uploadBtn.disabled = true;
                uploadBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Mengunggah...';
                
                // Show processing indicator after form submission
                const processingAlert = document.getElementById('upload-processing');
                if (processingAlert) {
                    setTimeout(function() {
                        processingAlert.classList.remove('d-none');
                    }, 1000); // Show after upload completes
                }
            }
        });
    }
}

/**
 * Format file size in a human-readable format
 */
function formatFileSize(bytes) {
    if (bytes < 1024) {
        return bytes + ' B';
    } else if (bytes < 1024 * 1024) {
        return (bytes / 1024).toFixed(1) + ' KB';
    } else if (bytes < 1024 * 1024 * 1024) {
        return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
    } else {
        return (bytes / (1024 * 1024 * 1024)).toFixed(1) + ' GB';
    }
}

/**
 * Initialize search functionality
 */
function initializeSearch() {
    const searchForm = document.getElementById('search-form');
    const searchInput = document.getElementById('search-input');
    const searchClear = document.getElementById('search-clear');
    
    if (searchInput && searchClear) {
        // Show clear button when search has input
        searchInput.addEventListener('input', function() {
            if (searchInput.value.length > 0) {
                searchClear.classList.remove('d-none');
            } else {
                searchClear.classList.add('d-none');
            }
        });
        
        // Clear search
        searchClear.addEventListener('click', function() {
            searchInput.value = '';
            searchClear.classList.add('d-none');
            
            // If on search results page, go back to dashboard
            if (window.location.pathname.includes('/search')) {
                window.location.href = '/dashboard';
            }
        });
    }
}

/**
 * Initialize Bootstrap tooltips
 */
function initializeTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

/**
 * Initialize file card functionality
 */
function initializeFileCards() {
    const fileCards = document.querySelectorAll('.file-card');
    
    fileCards.forEach(card => {
        card.addEventListener('click', function(e) {
            // Don't navigate if clicking on a button or link
            if (e.target.tagName === 'BUTTON' || e.target.tagName === 'A' || 
                e.target.closest('button') || e.target.closest('a')) {
                return;
            }
            
            const fileId = this.getAttribute('data-file-id');
            if (fileId) {
                window.location.href = `/files/${fileId}`;
            }
        });
    });
}

/**
 * Confirm file deletion
 */
function confirmDelete(fileId, fileName) {
    if (confirm(`Are you sure you want to delete "${fileName}"? This action cannot be undone.`)) {
        document.getElementById(`delete-form-${fileId}`).submit();
    }
}
