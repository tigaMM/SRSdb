// preview.js - JavaScript for file preview functionality

document.addEventListener('DOMContentLoaded', function() {
    // Initialize PDF viewer if present
    initializePdfViewer();
    
    // Initialize image viewer if present
    initializeImageViewer();
    
    // Initialize text preview if present
    initializeTextPreview();
});

/**
 * Initialize PDF.js viewer for PDF files
 */
function initializePdfViewer() {
    const pdfContainer = document.getElementById('pdf-viewer');
    
    if (pdfContainer) {
        const pdfUrl = pdfContainer.getAttribute('data-pdf-url');
        
        if (pdfUrl) {
            // Load PDF.js from CDN if not already loaded
            if (typeof pdfjsLib === 'undefined') {
                const script = document.createElement('script');
                script.src = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/2.12.313/pdf.min.js';
                document.head.appendChild(script);
                
                script.onload = function() {
                    // Initialize PDF.js
                    pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/2.12.313/pdf.worker.min.js';
                    loadPdf(pdfUrl);
                };
            } else {
                loadPdf(pdfUrl);
            }
        }
    }
}

/**
 * Load PDF document with PDF.js
 */
function loadPdf(pdfUrl) {
    const pdfContainer = document.getElementById('pdf-viewer');
    const loadingIndicator = document.getElementById('pdf-loading');
    
    if (loadingIndicator) {
        loadingIndicator.classList.remove('d-none');
    }
    
    // Load the PDF
    pdfjsLib.getDocument(pdfUrl).promise.then(function(pdf) {
        if (loadingIndicator) {
            loadingIndicator.classList.add('d-none');
        }
        
        // Create page navigation
        createPdfPageNav(pdf.numPages);
        
        // Load first page
        renderPdfPage(pdf, 1);
        
        // Add event listeners for page navigation
        document.getElementById('pdf-prev').addEventListener('click', function() {
            const currentPage = parseInt(document.getElementById('pdf-page-num').value);
            if (currentPage > 1) {
                renderPdfPage(pdf, currentPage - 1);
            }
        });
        
        document.getElementById('pdf-next').addEventListener('click', function() {
            const currentPage = parseInt(document.getElementById('pdf-page-num').value);
            if (currentPage < pdf.numPages) {
                renderPdfPage(pdf, currentPage + 1);
            }
        });
        
        document.getElementById('pdf-page-num').addEventListener('change', function() {
            const pageNumber = parseInt(this.value);
            if (pageNumber >= 1 && pageNumber <= pdf.numPages) {
                renderPdfPage(pdf, pageNumber);
            } else {
                this.value = document.getElementById('pdf-page-current').textContent;
            }
        });
    }).catch(function(error) {
        if (loadingIndicator) {
            loadingIndicator.classList.add('d-none');
        }
        
        pdfContainer.innerHTML = `<div class="alert alert-danger" role="alert">
            Failed to load PDF: ${error.message}
        </div>`;
    });
}

/**
 * Create PDF page navigation controls
 */
function createPdfPageNav(numPages) {
    const pdfNav = document.getElementById('pdf-nav');
    
    if (pdfNav) {
        pdfNav.classList.remove('d-none');
        document.getElementById('pdf-page-count').textContent = numPages;
    }
}

/**
 * Render a PDF page
 */
function renderPdfPage(pdf, pageNumber) {
    const pdfContainer = document.getElementById('pdf-viewer');
    const canvas = document.createElement('canvas');
    const context = canvas.getContext('2d');
    const loadingIndicator = document.getElementById('pdf-page-loading');
    
    // Update page navigation
    document.getElementById('pdf-page-current').textContent = pageNumber;
    document.getElementById('pdf-page-num').value = pageNumber;
    
    // Show loading indicator
    if (loadingIndicator) {
        loadingIndicator.classList.remove('d-none');
    }
    
    // Remove previous canvas
    while (pdfContainer.firstChild) {
        pdfContainer.removeChild(pdfContainer.firstChild);
    }
    
    // Add new canvas
    pdfContainer.appendChild(canvas);
    
    // Get the page
    pdf.getPage(pageNumber).then(function(page) {
        // Hide loading indicator
        if (loadingIndicator) {
            loadingIndicator.classList.add('d-none');
        }
        
        // Determine scale to fit within container
        const viewport = page.getViewport({ scale: 1 });
        const containerWidth = pdfContainer.clientWidth;
        const scale = containerWidth / viewport.width;
        const scaledViewport = page.getViewport({ scale: scale });
        
        // Set canvas dimensions
        canvas.width = scaledViewport.width;
        canvas.height = scaledViewport.height;
        
        // Render the page
        const renderContext = {
            canvasContext: context,
            viewport: scaledViewport
        };
        
        page.render(renderContext);
    });
}

/**
 * Initialize image viewer
 */
function initializeImageViewer() {
    const imageContainer = document.getElementById('image-viewer');
    
    if (imageContainer) {
        const imageUrl = imageContainer.getAttribute('data-image-url');
        
        if (imageUrl) {
            const img = document.createElement('img');
            img.src = imageUrl;
            img.className = 'img-fluid';
            img.alt = 'Image preview';
            
            imageContainer.appendChild(img);
        }
    }
}

/**
 * Initialize text preview with syntax highlighting
 */
function initializeTextPreview() {
    const textContainer = document.getElementById('text-preview');
    
    if (textContainer) {
        const textContent = textContainer.getAttribute('data-text-content');
        const fileType = textContainer.getAttribute('data-file-type');
        
        if (textContent) {
            // Determine if we should use syntax highlighting
            const syntaxHighlightTypes = {
                'json': 'json',
                'xml': 'xml',
                'html': 'html',
                'css': 'css',
                'js': 'javascript',
                'py': 'python',
                'md': 'markdown'
            };
            
            const language = syntaxHighlightTypes[fileType] || 'plaintext';
            
            // If Prism.js is available, use it for syntax highlighting
            if (typeof Prism !== 'undefined') {
                textContainer.innerHTML = `<pre><code class="language-${language}">${textContent}</code></pre>`;
                Prism.highlightAll();
            } else {
                // Otherwise, use a simple pre tag
                textContainer.innerHTML = `<pre>${textContent}</pre>`;
            }
        }
    }
}
