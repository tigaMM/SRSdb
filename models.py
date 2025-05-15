from datetime import datetime
from app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    is_guest = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship with files
    files = db.relationship('File', backref='owner', lazy='dynamic')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'


class File(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_type = db.Column(db.String(50), nullable=False)
    file_size = db.Column(db.Integer, nullable=False)  # Size in bytes
    mime_type = db.Column(db.String(100), nullable=False)
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)
    last_accessed = db.Column(db.DateTime, nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Relationship with file_meta ('metadata' is a reserved word in SQLAlchemy)
    file_meta = db.relationship('FileMetadata', backref='file', uselist=False, cascade="all, delete-orphan")
    
    def __repr__(self):
        return f'<File {self.original_filename}>'


class FileMetadata(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    file_id = db.Column(db.Integer, db.ForeignKey('file.id'), nullable=False)
    
    # Common metadata
    title = db.Column(db.String(255), nullable=True)
    description = db.Column(db.Text, nullable=True)
    keywords = db.Column(db.String(500), nullable=True)
    extracted_text = db.Column(db.Text, nullable=True)
    
    # Document-specific metadata
    author = db.Column(db.String(255), nullable=True)
    page_count = db.Column(db.Integer, nullable=True)
    
    # Image-specific metadata
    width = db.Column(db.Integer, nullable=True)
    height = db.Column(db.Integer, nullable=True)
    
    # AI-extracted data
    ai_tags = db.Column(db.String(500), nullable=True)
    ai_summary = db.Column(db.Text, nullable=True)
    ai_processed = db.Column(db.Boolean, default=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<FileMetadata for file_id={self.file_id}>'
