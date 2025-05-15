import os
import json
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime

# Mendapatkan URL database dari variabel lingkungan
DATABASE_URL = os.environ.get('DATABASE_URL')

def get_connection():
    """Membuat koneksi ke database PostgreSQL"""
    try:
        return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    except Exception as e:
        print(f"Error koneksi database: {str(e)}")
        return None

def create_file_metadata(file_data):
    """
    Menyimpan metadata file ke database PostgreSQL
    
    file_data: dict dengan fields:
        - filename: nama file yang disimpan di server
        - original_filename: nama file asli yang diupload
        - file_type: tipe file (extension)
        - file_size: ukuran file dalam bytes
        - content_type: MIME type
        - summary: ringkasan AI dari isi file (opsional)
        - word_count: jumlah kata dalam file (opsional)
    """
    if not DATABASE_URL:
        print("DATABASE_URL tidak ditemukan")
        return None
    
    conn = get_connection()
    if not conn:
        return None
    
    try:
        cursor = conn.cursor()
        
        # Siapkan kolom dan nilai untuk query SQL
        columns = []
        values = []
        placeholders = []
        
        for key, value in file_data.items():
            if key in ['filename', 'original_filename', 'file_type', 'file_size', 'content_type', 
                      'summary', 'word_count', 'keywords', 'width', 'height']:
                columns.append(key)
                values.append(value)
                placeholders.append('%s')
        
        # Buat query SQL
        query = f"""
            INSERT INTO files ({', '.join(columns)})
            VALUES ({', '.join(placeholders)})
            RETURNING *
        """
        
        # Eksekusi query
        cursor.execute(query, values)
        result = cursor.fetchone()
        
        # Commit perubahan
        conn.commit()
        
        return dict(result)
    except Exception as e:
        print(f"Error menyimpan ke database: {str(e)}")
        conn.rollback()
        return None
    finally:
        conn.close()

def get_all_files():
    """
    Mendapatkan semua metadata file dari database
    """
    if not DATABASE_URL:
        print("DATABASE_URL tidak ditemukan")
        return []
    
    conn = get_connection()
    if not conn:
        return []
    
    try:
        cursor = conn.cursor()
        
        # Query untuk mengambil semua file, diurutkan berdasarkan waktu upload (terbaru dulu)
        query = """
            SELECT * FROM files
            ORDER BY created_at DESC
        """
        
        # Eksekusi query
        cursor.execute(query)
        results = cursor.fetchall()
        
        # Ubah hasil ke format list of dictionaries
        return [dict(row) for row in results]
    except Exception as e:
        print(f"Error mengambil data dari database: {str(e)}")
        return []
    finally:
        conn.close()

def get_file_by_filename(filename):
    """
    Mendapatkan metadata file berdasarkan nama file
    """
    if not DATABASE_URL:
        print("DATABASE_URL tidak ditemukan")
        return None
    
    conn = get_connection()
    if not conn:
        return None
    
    try:
        cursor = conn.cursor()
        
        # Query untuk mencari file berdasarkan nama file
        query = """
            SELECT * FROM files
            WHERE filename = %s
            LIMIT 1
        """
        
        # Eksekusi query
        cursor.execute(query, (filename,))
        result = cursor.fetchone()
        
        # Jika hasil ditemukan, ubah ke dictionary
        if result:
            return dict(result)
        return None
    except Exception as e:
        print(f"Error mengambil data dari database: {str(e)}")
        return None
    finally:
        conn.close()

def delete_file_metadata(filename):
    """
    Menghapus metadata file dari database
    """
    if not DATABASE_URL:
        print("DATABASE_URL tidak ditemukan")
        return False
    
    conn = get_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        
        # Query untuk menghapus file berdasarkan nama file
        query = """
            DELETE FROM files
            WHERE filename = %s
            RETURNING id
        """
        
        # Eksekusi query
        cursor.execute(query, (filename,))
        result = cursor.fetchone()
        
        # Commit perubahan
        conn.commit()
        
        # Jika ada baris yang dihapus, berarti berhasil
        return result is not None
    except Exception as e:
        print(f"Error menghapus data dari database: {str(e)}")
        conn.rollback()
        return False
    finally:
        conn.close()