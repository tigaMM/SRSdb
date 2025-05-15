import os
import uuid
import sys
from flask import Flask, render_template, request, redirect, url_for, send_from_directory, flash, jsonify
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

# Tambahkan path ke direktori sistem
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import supabase_utils
import database_utils
import ai_utils

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__, static_folder='static')
app.secret_key = os.environ.get('SECRET_KEY', 'smartfilevault-dev-key')

# Direktori untuk menyimpan file yang diupload
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Ukuran upload maksimum: 16MB
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

# Ekstensi file yang diizinkan
ALLOWED_EXTENSIONS = {
    'txt', 'pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx',
    'png', 'jpg', 'jpeg', 'gif', 'bmp', 'svg',
    'csv', 'json', 'xml', 'md'
}

def allowed_file(filename):
    """Cek apakah ekstensi file diizinkan"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_file_extension(filename):
    """Dapatkan ekstensi file"""
    return filename.rsplit('.', 1)[1].lower() if '.' in filename else ''

def get_file_icon(file_type):
    """Dapatkan ikon untuk tipe file"""
    icon_map = {
        'pdf': 'document-text',
        'doc': 'document',
        'docx': 'document',
        'txt': 'document-text',
        'jpg': 'photograph',
        'jpeg': 'photograph',
        'png': 'photograph',
        'gif': 'photograph',
        'xls': 'table',
        'xlsx': 'table',
        'csv': 'table',
        'ppt': 'presentation',
        'pptx': 'presentation',
    }
    return icon_map.get(file_type, 'document')

def format_file_size(size_in_bytes):
    """Format ukuran file ke bentuk yang lebih mudah dibaca"""
    if size_in_bytes < 1024:
        return f"{size_in_bytes} B"
    elif size_in_bytes < 1024 * 1024:
        return f"{size_in_bytes / 1024:.1f} KB"
    elif size_in_bytes < 1024 * 1024 * 1024:
        return f"{size_in_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_in_bytes / (1024 * 1024 * 1024):.1f} GB"

def preview_file(file_path, file_type):
    """Generate preview untuk file berdasarkan tipe"""
    # Fix untuk error pada file preview:
    # Type error: Argument of type "dict[Any, Any]" cannot be assigned to parameter "value" of type "str"
    if file_type in ['jpg', 'jpeg', 'png', 'gif', 'bmp']:
        return {'type': 'image'}
    elif file_type == 'pdf':
        return {'type': 'pdf'}
    elif file_type in ['txt', 'csv', 'md']:
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read(10000)  # Batasi ke 10KB untuk preview
                return {
                    'type': 'text',
                    'content': content
                }
        except Exception as e:
            print(f"Error membaca file teks: {str(e)}")
            return {'type': 'error', 'message': str(e)}
    else:
        return {'type': 'unsupported'}

@app.route('/')
def index():
    """Halaman utama/dashboard"""
    files = database_utils.get_all_files()
    return render_template('dashboard.html', files=files, get_file_icon=get_file_icon)

@app.route('/upload', methods=['POST'])
def upload_file():
    """Handler untuk upload file"""
    if 'file' not in request.files:
        flash('Tidak ada file yang dipilih', 'danger')
        return redirect(url_for('index'))
    
    file = request.files['file']
    
    if file.filename == '':
        flash('Tidak ada file yang dipilih', 'danger')
        return redirect(url_for('index'))
    
    if file and allowed_file(file.filename):
        # Amankan nama file dan dapatkan informasi file
        original_filename = secure_filename(file.filename or "")
        file_ext = get_file_extension(original_filename)
        
        # Buat nama file unik untuk penyimpanan
        unique_filename = f"{uuid.uuid4().hex}.{file_ext}"
        file_path = os.path.join(UPLOAD_FOLDER, unique_filename)
        
        # Simpan file ke disk
        file.save(file_path)
        file_size = os.path.getsize(file_path)
        
        # Analisis file dengan AI
        ai_result = ai_utils.analyze_file(file_path)
        
        # Siapkan data untuk disimpan ke Supabase
        file_data = {
            'filename': unique_filename,
            'original_filename': original_filename,
            'file_type': file_ext,
            'file_size': file_size,
            'content_type': file.content_type,
            'summary': ai_result.get('summary', ''),
            'word_count': ai_result.get('word_count', 0),
            'keywords': ','.join(ai_result.get('keywords', [])),
        }
        
        # Tambahkan metadata tambahan untuk gambar
        if ai_result.get('type') == 'image':
            file_data['width'] = ai_result.get('width', 0)
            file_data['height'] = ai_result.get('height', 0)
        
        # Simpan metadata ke database PostgreSQL
        stored_data = database_utils.create_file_metadata(file_data)
        
        if stored_data:
            flash('File berhasil diupload dan dianalisis', 'success')
        else:
            flash('File berhasil diupload, tapi gagal menyimpan metadata', 'warning')
        
        return redirect(url_for('index'))
    
    flash('Tipe file tidak diizinkan', 'danger')
    return redirect(url_for('index'))

@app.route('/download/<filename>')
def download_file(filename):
    """Download file yang sudah diupload"""
    # Dapatkan metadata file dari database
    file_data = database_utils.get_file_by_filename(filename)
    
    if not file_data:
        flash('File tidak ditemukan', 'danger')
        return redirect(url_for('index'))
    
    # Kirim file dengan nama aslinya
    return send_from_directory(
        UPLOAD_FOLDER, 
        filename, 
        as_attachment=True,
        download_name=file_data.get('original_filename')
    )

@app.route('/view/<filename>')
def view_file(filename):
    """Tampilkan preview file"""
    # Dapatkan metadata file dari database
    file_data = database_utils.get_file_by_filename(filename)
    
    if not file_data:
        flash('File tidak ditemukan', 'danger')
        return redirect(url_for('index'))
    
    # Path file yang tersimpan
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    
    if not os.path.exists(file_path):
        flash('File tidak ditemukan di server', 'danger')
        return redirect(url_for('index'))
    
    # Dapatkan informasi preview
    preview_info = preview_file(file_path, file_data.get('file_type', ''))
    # Menyimpan file data secara terpisah, bukan sebagai bagian dari preview_info
    # untuk menghindari error type dict[Any, Any] ke str
    
    # Format ukuran file untuk tampilan
    file_data['formatted_size'] = format_file_size(file_data.get('file_size', 0))
    
    return render_template('view.html', file=file_data, preview=preview_info, get_file_icon=get_file_icon)

@app.route('/delete/<filename>', methods=['POST'])
def delete_file(filename):
    """Hapus file"""
    # Dapatkan metadata file dari database
    file_data = database_utils.get_file_by_filename(filename)
    
    if not file_data:
        flash('File tidak ditemukan', 'danger')
        return redirect(url_for('index'))
    
    # Path file yang tersimpan
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    
    # Hapus file dari disk
    if os.path.exists(file_path):
        os.remove(file_path)
    
    # Hapus metadata dari database
    if database_utils.delete_file_metadata(filename):
        flash('File berhasil dihapus', 'success')
    else:
        flash('File dihapus dari server, tapi gagal menghapus metadata', 'warning')
    
    return redirect(url_for('index'))

@app.route('/api/files')
def api_files():
    """API endpoint untuk mendapatkan daftar file"""
    files = database_utils.get_all_files()
    return jsonify(files)

@app.route('/api/files/<filename>')
def api_file_detail(filename):
    """API endpoint untuk mendapatkan detail file"""
    file = database_utils.get_file_by_filename(filename)
    if file:
        return jsonify(file)
    return jsonify({'error': 'File tidak ditemukan'}), 404

if __name__ == '__main__':
    # Run aplikasi
    app.run(host='0.0.0.0', port=5000, debug=True)