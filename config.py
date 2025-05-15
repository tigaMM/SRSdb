import os

# File extensions that are allowed to be uploaded
ALLOWED_EXTENSIONS = {
    'txt', 'pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx',
    'png', 'jpg', 'jpeg', 'gif', 'bmp', 'svg',
    'csv', 'json', 'xml', 'html', 'md'
}

# File types and their categories for display and processing
FILE_CATEGORIES = {
    'document': ['txt', 'pdf', 'doc', 'docx', 'ppt', 'pptx', 'md'],
    'spreadsheet': ['xls', 'xlsx', 'csv'],
    'image': ['png', 'jpg', 'jpeg', 'gif', 'bmp', 'svg'],
    'code': ['json', 'xml', 'html', 'py', 'js', 'css']
}

# MIME types for better file handling
MIME_TYPES = {
    'txt': 'text/plain',
    'pdf': 'application/pdf',
    'doc': 'application/msword',
    'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'xls': 'application/vnd.ms-excel',
    'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'ppt': 'application/vnd.ms-powerpoint',
    'pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
    'png': 'image/png',
    'jpg': 'image/jpeg',
    'jpeg': 'image/jpeg',
    'gif': 'image/gif',
    'bmp': 'image/bmp',
    'svg': 'image/svg+xml',
    'csv': 'text/csv',
    'json': 'application/json',
    'xml': 'application/xml',
    'html': 'text/html',
    'md': 'text/markdown'
}

# Determine if a file extension is allowed
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Get file category based on extension
def get_file_category(filename):
    if '.' not in filename:
        return 'unknown'
    
    extension = filename.rsplit('.', 1)[1].lower()
    
    for category, extensions in FILE_CATEGORIES.items():
        if extension in extensions:
            return category
    
    return 'other'

# Get MIME type based on file extension
def get_mime_type(filename):
    if '.' not in filename:
        return 'application/octet-stream'
    
    extension = filename.rsplit('.', 1)[1].lower()
    return MIME_TYPES.get(extension, 'application/octet-stream')
