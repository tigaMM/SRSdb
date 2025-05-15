import os
import json
import requests
from datetime import datetime

# Mendapatkan konfigurasi Supabase dari variabel lingkungan
SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY')

# Nama tabel di Supabase
FILES_TABLE = 'files'

def create_file_metadata(file_data):
    """
    Menyimpan metadata file ke Supabase
    
    file_data: dict dengan fields:
        - filename: nama file yang disimpan di server
        - original_filename: nama file asli yang diupload
        - file_type: tipe file (extension)
        - file_size: ukuran file dalam bytes
        - content_type: MIME type
        - summary: ringkasan AI dari isi file (opsional)
        - word_count: jumlah kata dalam file (opsional)
        - user_id: ID pengguna yang mengupload (opsional)
    """
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("Konfigurasi Supabase belum lengkap")
        return None
    
    # Tambahkan timestamp upload
    file_data['created_at'] = datetime.now().isoformat()
    
    # Endpoint API Supabase untuk tabel files
    api_endpoint = f"{SUPABASE_URL}/rest/v1/{FILES_TABLE}"
    
    # Headers untuk autentikasi Supabase
    headers = {
        'apikey': SUPABASE_KEY,
        'Authorization': f'Bearer {SUPABASE_KEY}',
        'Content-Type': 'application/json',
        'Prefer': 'return=representation'
    }
    
    try:
        # Kirim data ke Supabase menggunakan REST API
        response = requests.post(
            api_endpoint,
            headers=headers,
            data=json.dumps(file_data)
        )
        
        # Periksa status response
        if response.status_code == 201:
            return response.json()[0]
        else:
            print(f"Error menyimpan ke Supabase: {response.status_code}")
            print(response.text)
            return None
    except Exception as e:
        print(f"Error koneksi Supabase: {str(e)}")
        return None

def get_all_files():
    """
    Mendapatkan semua metadata file dari Supabase
    """
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("Konfigurasi Supabase belum lengkap")
        return []
    
    # Endpoint API Supabase untuk tabel files
    api_endpoint = f"{SUPABASE_URL}/rest/v1/{FILES_TABLE}"
    
    # Headers untuk autentikasi Supabase
    headers = {
        'apikey': SUPABASE_KEY,
        'Authorization': f'Bearer {SUPABASE_KEY}'
    }
    
    try:
        # Ambil data dari Supabase menggunakan REST API
        response = requests.get(
            api_endpoint,
            headers=headers,
            params={
                'order': 'created_at.desc'  # Urutkan berdasarkan waktu upload (terbaru dulu)
            }
        )
        
        # Periksa status response
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error mengambil data dari Supabase: {response.status_code}")
            print(response.text)
            return []
    except Exception as e:
        print(f"Error koneksi Supabase: {str(e)}")
        return []

def get_file_by_filename(filename):
    """
    Mendapatkan metadata file berdasarkan nama file
    """
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("Konfigurasi Supabase belum lengkap")
        return None
    
    # Endpoint API Supabase untuk tabel files
    api_endpoint = f"{SUPABASE_URL}/rest/v1/{FILES_TABLE}"
    
    # Headers untuk autentikasi Supabase
    headers = {
        'apikey': SUPABASE_KEY,
        'Authorization': f'Bearer {SUPABASE_KEY}'
    }
    
    try:
        # Ambil data dari Supabase menggunakan REST API dengan filter
        response = requests.get(
            api_endpoint,
            headers=headers,
            params={
                'filename': f'eq.{filename}',
                'limit': 1
            }
        )
        
        # Periksa status response
        if response.status_code == 200:
            data = response.json()
            if data:
                return data[0]
            return None
        else:
            print(f"Error mengambil data dari Supabase: {response.status_code}")
            print(response.text)
            return None
    except Exception as e:
        print(f"Error koneksi Supabase: {str(e)}")
        return None

def delete_file_metadata(filename):
    """
    Menghapus metadata file dari Supabase
    """
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("Konfigurasi Supabase belum lengkap")
        return False
    
    # Endpoint API Supabase untuk tabel files
    api_endpoint = f"{SUPABASE_URL}/rest/v1/{FILES_TABLE}"
    
    # Headers untuk autentikasi Supabase
    headers = {
        'apikey': SUPABASE_KEY,
        'Authorization': f'Bearer {SUPABASE_KEY}'
    }
    
    try:
        # Hapus data dari Supabase menggunakan REST API dengan filter
        response = requests.delete(
            api_endpoint,
            headers=headers,
            params={
                'filename': f'eq.{filename}'
            }
        )
        
        # Periksa status response
        if response.status_code == 200 or response.status_code == 204:
            return True
        else:
            print(f"Error menghapus data dari Supabase: {response.status_code}")
            print(response.text)
            return False
    except Exception as e:
        print(f"Error koneksi Supabase: {str(e)}")
        return False