import os
import mimetypes
from app import app
from werkzeug.utils import secure_filename
import base64

def get_file_preview(file):
    """
    Get preview information for a file.
    Returns a tuple of (preview_type, preview_data)
    """
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    file_type = file.file_type.lower()
    
    # Check if file exists
    if not os.path.exists(file_path):
        return 'error', 'File not found'
    
    # Handle different file types
    if file_type in ['jpg', 'jpeg', 'png', 'gif', 'bmp']:
        return 'image', url_for_file(file)
    
    elif file_type == 'pdf':
        return 'pdf', url_for_file(file)
    
    elif file_type in ['doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx']:
        # For Office documents, we might not have a direct preview
        # Just return metadata and download link
        return 'document', {
            'filename': file.original_filename,
            'file_type': file.file_type,
            'file_size': format_file_size(file.file_size),
            'mime_type': file.mime_type,
            'download_url': f'/download/{file.id}'
        }
    
    elif file_type in ['txt', 'csv', 'json', 'xml', 'html', 'md']:
        # For text files, we can try to read and display the content
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read(10000)  # Limit to first 10KB to avoid large files
                return 'text', content
        except Exception as e:
            app.logger.error(f"Error reading text file {file_path}: {str(e)}")
            return 'error', f"Could not read file: {str(e)}"
    
    else:
        # For unknown types, just show metadata
        return 'unknown', {
            'filename': file.original_filename,
            'file_type': file.file_type,
            'file_size': format_file_size(file.file_size),
            'mime_type': file.mime_type
        }

def get_file_thumbnail(file):
    """Generate a thumbnail or icon for a file."""
    file_type = file.file_type.lower()
    
    # For images, use the actual image as thumbnail
    if file_type in ['jpg', 'jpeg', 'png', 'gif', 'bmp']:
        return f'/files/{file.id}/raw'
    
    # For other file types, return an appropriate icon class
    icon_map = {
        'pdf': 'file-pdf',
        'doc': 'file-word',
        'docx': 'file-word',
        'xls': 'file-excel',
        'xlsx': 'file-excel',
        'ppt': 'file-powerpoint',
        'pptx': 'file-powerpoint',
        'txt': 'file-text',
        'csv': 'file-csv',
        'zip': 'file-archive',
        'rar': 'file-archive',
        'mp3': 'file-audio',
        'mp4': 'file-video',
        'json': 'file-code',
        'xml': 'file-code',
        'html': 'file-code',
    }
    
    return icon_map.get(file_type, 'file')

def format_file_size(size_in_bytes):
    """Format file size in a human-readable format."""
    if size_in_bytes < 1024:
        return f"{size_in_bytes} B"
    elif size_in_bytes < 1024 * 1024:
        return f"{size_in_bytes / 1024:.1f} KB"
    elif size_in_bytes < 1024 * 1024 * 1024:
        return f"{size_in_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_in_bytes / (1024 * 1024 * 1024):.1f} GB"

def url_for_file(file):
    """Generate URL for accessing a file."""
    return f'/files/{file.id}/raw'

def is_file_text_previewable(file_type):
    """Check if a file type can be previewed as text."""
    text_previewable = ['txt', 'csv', 'json', 'xml', 'html', 'md', 'py', 'js', 'css']
    return file_type.lower() in text_previewable
