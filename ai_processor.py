import os
import re
import nltk
from app import app, db
from models import File, FileMetadata
import PyPDF2
from PIL import Image
import docx
import spacy

# Initialize NLP components
try:
    nltk.download('punkt', quiet=True)
    nltk.download('stopwords', quiet=True)
    from nltk.corpus import stopwords
    from nltk.tokenize import word_tokenize, sent_tokenize
    
    # Load spaCy model - using the small English model
    try:
        nlp = spacy.load("en_core_web_sm")
    except:
        # If the model is not installed, use a basic pipeline
        nlp = spacy.blank("en")
        app.logger.warning("SpaCy model not found. Using basic pipeline instead.")
except Exception as e:
    app.logger.error(f"Error initializing NLP components: {str(e)}")
    # Define fallback functions in case NLTK fails to load
    def word_tokenize(text):
        return text.split()
    def sent_tokenize(text):
        return re.split(r'(?<=[.!?])\s+', text)
    stopwords = {'english': set()}
    nlp = None

def extract_text_from_pdf(file_path):
    """Extract text content from a PDF file."""
    try:
        text = ""
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                text += page.extract_text() + "\n"
        return text
    except Exception as e:
        app.logger.error(f"Error extracting text from PDF {file_path}: {str(e)}")
        return ""

def extract_text_from_docx(file_path):
    """Extract text content from a DOCX file."""
    try:
        doc = docx.Document(file_path)
        return "\n".join([paragraph.text for paragraph in doc.paragraphs])
    except Exception as e:
        app.logger.error(f"Error extracting text from DOCX {file_path}: {str(e)}")
        return ""

def extract_text_from_txt(file_path):
    """Extract text content from a plain text file."""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
            return file.read()
    except Exception as e:
        app.logger.error(f"Error extracting text from TXT {file_path}: {str(e)}")
        return ""

def extract_image_metadata(file_path):
    """Extract metadata from an image file."""
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
        app.logger.error(f"Error extracting metadata from image {file_path}: {str(e)}")
        return {}

def extract_keywords(text, max_keywords=10):
    """Extract important keywords from text."""
    if not text or not nlp:
        return []
    
    try:
        # Process with spaCy
        doc = nlp(text[:10000])  # Limit text length to avoid processing too much
        
        # Extract entities and noun chunks as potential keywords
        keywords = []
        
        # Get named entities
        entities = [ent.text for ent in doc.ents]
        
        # Get noun chunks
        noun_chunks = [chunk.text for chunk in doc.noun_chunks]
        
        # Combine and deduplicate
        potential_keywords = set(entities + noun_chunks)
        
        # Clean and filter keywords
        stop_words = set(stopwords.words('english')) if hasattr(stopwords, 'words') else set()
        keywords = [
            kw.lower() for kw in potential_keywords 
            if len(kw) > 2 and not all(token.lower() in stop_words for token in word_tokenize(kw))
        ]
        
        # Limit number of keywords
        return list(set(keywords))[:max_keywords]
    except Exception as e:
        app.logger.error(f"Error extracting keywords: {str(e)}")
        return []

def generate_summary(text, max_sentences=3):
    """Generate a brief summary from text."""
    if not text:
        return ""
    
    try:
        # Split text into sentences
        sentences = sent_tokenize(text)
        
        if len(sentences) <= max_sentences:
            return text
        
        # For a simple summary, just take the first few sentences
        summary = " ".join(sentences[:max_sentences])
        
        return summary
    except Exception as e:
        app.logger.error(f"Error generating summary: {str(e)}")
        return text[:200] + "..." if len(text) > 200 else text

def process_file_with_ai(file_id, file_path):
    """Process a file with AI to extract metadata."""
    try:
        file = File.query.get(file_id)
        if not file:
            app.logger.error(f"File with ID {file_id} not found")
            return
        
        metadata = file.file_meta
        if not metadata:
            metadata = FileMetadata(file_id=file_id)
            db.session.add(metadata)
        
        file_type = file.file_type.lower()
        extracted_text = ""
        
        # Extract text based on file type
        if file_type == 'pdf':
            extracted_text = extract_text_from_pdf(file_path)
            # Get page count for PDFs
            try:
                with open(file_path, 'rb') as pdf_file:
                    pdf_reader = PyPDF2.PdfReader(pdf_file)
                    metadata.page_count = len(pdf_reader.pages)
            except:
                pass
        elif file_type in ['doc', 'docx']:
            extracted_text = extract_text_from_docx(file_path)
        elif file_type == 'txt':
            extracted_text = extract_text_from_txt(file_path)
        elif file_type in ['png', 'jpg', 'jpeg', 'gif', 'bmp']:
            # For images, extract metadata
            image_info = extract_image_metadata(file_path)
            metadata.width = image_info.get('width')
            metadata.height = image_info.get('height')
            
        # Store extracted text
        metadata.extracted_text = extracted_text[:10000]  # Limit stored text
        
        # Extract keywords
        keywords = extract_keywords(extracted_text)
        metadata.keywords = ", ".join(keywords)
        
        # Generate summary
        summary = generate_summary(extracted_text)
        metadata.ai_summary = summary
        
        # Set AI tags (using keywords for now)
        metadata.ai_tags = ", ".join(keywords[:5])
        
        # Set title if not present
        if not metadata.title:
            # Use original filename without extension as title
            metadata.title = os.path.splitext(file.original_filename)[0]
        
        # Mark as processed
        metadata.ai_processed = True
        
        # Save changes to database
        db.session.commit()
        
        app.logger.info(f"Successfully processed file {file_id} with AI")
    except Exception as e:
        app.logger.error(f"Error processing file {file_id} with AI: {str(e)}")
        db.session.rollback()
