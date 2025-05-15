import os
import re
import PyPDF2
from PIL import Image
import docx
import nltk
from collections import Counter

# Download nltk data jika belum ada
try:
    nltk.download('punkt', quiet=True)
except:
    pass  # handle offline case

def count_words(text):
    """
    Menghitung jumlah kata dalam teks
    """
    if not text:
        return 0
    words = nltk.word_tokenize(text)
    return len(words)

def extract_keywords(text, max_keywords=5):
    """
    Ekstrak kata kunci dari teks
    """
    if not text:
        return []
    
    # Lowercase dan bersihkan teks
    text = text.lower()
    # Hapus tanda baca dan angka
    text = re.sub(r'[^\w\s]', '', text)
    text = re.sub(r'\d+', '', text)
    
    # Tokenisasi
    words = nltk.word_tokenize(text)
    
    # Filter stopwords (kata umum)
    stopwords = set(['dan', 'atau', 'yang', 'di', 'ke', 'pada', 'untuk', 'dari', 'dengan', 
                     'adalah', 'ini', 'itu', 'oleh', 'akan', 'tidak', 'telah', 'sebagai',
                     'and', 'or', 'the', 'a', 'an', 'is', 'in', 'to', 'of', 'for', 'by', 
                     'on', 'at', 'from', 'with', 'that', 'this', 'be', 'are', 'were', 'was'])
    
    filtered_words = [word for word in words if word not in stopwords and len(word) > 3]
    
    # Hitung frekuensi kata
    word_freq = Counter(filtered_words)
    
    # Ambil kata-kata terbanyak
    return [word for word, _ in word_freq.most_common(max_keywords)]

def generate_summary(text, max_length=150):
    """
    Menghasilkan ringkasan teks sederhana
    """
    if not text or len(text) <= max_length:
        return text
    
    # Ambil kalimat pertama (biasanya kalimat pembuka berisi informasi penting)
    sentences = nltk.sent_tokenize(text)
    
    if not sentences:
        return text[:max_length] + "..."
    
    # Ambil kalimat pertama + potong jika terlalu panjang
    summary = sentences[0]
    if len(summary) > max_length:
        return summary[:max_length] + "..."
    
    # Tambahkan kalimat sampai mendekati max_length
    current_length = len(summary)
    for sentence in sentences[1:]:
        if current_length + len(sentence) + 1 > max_length:
            break
        summary += " " + sentence
        current_length += len(sentence) + 1
    
    return summary

def extract_text_from_pdf(file_path):
    """
    Ekstrak teks dari file PDF
    """
    try:
        text = ""
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page_num in range(len(pdf_reader.pages)):
                text += pdf_reader.pages[page_num].extract_text() + "\n"
        return text
    except Exception as e:
        print(f"Error membaca PDF: {str(e)}")
        return ""

def extract_text_from_docx(file_path):
    """
    Ekstrak teks dari file DOCX
    """
    try:
        doc = docx.Document(file_path)
        return "\n".join([paragraph.text for paragraph in doc.paragraphs])
    except Exception as e:
        print(f"Error membaca DOCX: {str(e)}")
        return ""

def extract_text_from_txt(file_path):
    """
    Ekstrak teks dari file TXT
    """
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
            return file.read()
    except Exception as e:
        print(f"Error membaca TXT: {str(e)}")
        return ""

def extract_image_metadata(file_path):
    """
    Ekstrak metadata dari file gambar
    """
    try:
        with Image.open(file_path) as img:
            width, height = img.size
            format_name = img.format
            mode = img.mode
            return {
                'width': width,
                'height': height,
                'format': format_name,
                'mode': mode
            }
    except Exception as e:
        print(f"Error membaca metadata gambar: {str(e)}")
        return {}

def analyze_file(file_path):
    """
    Analisis file dan ekstrak informasi penting
    """
    file_extension = os.path.splitext(file_path)[1].lower()
    
    # Inisialisasi hasil dengan default
    result = {
        'word_count': 0,
        'summary': '',
        'keywords': [],
        'type': 'other'
    }
    
    # Proses berdasarkan tipe file
    if file_extension in ['.pdf']:
        result['type'] = 'document'
        text = extract_text_from_pdf(file_path)
        if text:
            result['word_count'] = count_words(text)
            result['summary'] = generate_summary(text)
            result['keywords'] = extract_keywords(text)
    
    elif file_extension in ['.docx', '.doc']:
        result['type'] = 'document'
        text = extract_text_from_docx(file_path)
        if text:
            result['word_count'] = count_words(text)
            result['summary'] = generate_summary(text)
            result['keywords'] = extract_keywords(text)
    
    elif file_extension in ['.txt', '.md', '.csv']:
        result['type'] = 'text'
        text = extract_text_from_txt(file_path)
        if text:
            result['word_count'] = count_words(text)
            result['summary'] = generate_summary(text)
            result['keywords'] = extract_keywords(text)
    
    elif file_extension in ['.jpg', '.jpeg', '.png', '.gif', '.bmp']:
        result['type'] = 'image'
        img_metadata = extract_image_metadata(file_path)
        
        # Update hasil dengan metadata gambar
        result.update(img_metadata)
        result['summary'] = f"Gambar {img_metadata.get('format', 'Unknown')} dengan resolusi {img_metadata.get('width', 0)}×{img_metadata.get('height', 0)}."
    
    return result