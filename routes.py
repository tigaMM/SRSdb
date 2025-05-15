import os
import uuid
import logging
from datetime import datetime
from flask import render_template, request, redirect, url_for, flash, jsonify, send_from_directory, abort
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from app import app, db
from models import User, File, FileMetadata
from config import allowed_file, get_file_category, get_mime_type
from file_handler import get_file_preview, get_file_thumbnail
from ai_processor import process_file_with_ai

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        logger.info(f"Already authenticated user {current_user.username} redirected to dashboard")
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user, remember=True)
            logger.info(f"User {username} logged in successfully (Admin: {user.is_admin}, Guest: {user.is_guest})")
            next_page = request.args.get('next')
            return redirect(next_page or url_for('dashboard'))
        else:
            if user:
                logger.warning(f"Failed login attempt for user {username} - Invalid password")
            else:
                logger.warning(f"Failed login attempt for non-existent user {username}")
            flash('Invalid username or password', 'danger')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if password != confirm_password:
            flash('Passwords do not match', 'danger')
            return render_template('register.html')
            
        existing_user = User.query.filter((User.username == username) | (User.email == email)).first()
        if existing_user:
            flash('Username or email already exists', 'danger')
            return render_template('register.html')
            
        user = User(username=username, email=email)
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful! You can now log in.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    if current_user.is_authenticated:
        username = current_user.username
        logger.info(f"User {username} logged out")
    logout_user()
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    # Admin dapat melihat semua file
    if current_user.is_admin:
        files = File.query.order_by(File.upload_date.desc()).all()
    else:
        # User biasa atau guest hanya melihat file mereka sendiri
        files = File.query.filter_by(user_id=current_user.id).order_by(File.upload_date.desc()).all()
    
    file_categories = {}
    
    for file in files:
        category = get_file_category(file.original_filename)
        if category not in file_categories:
            file_categories[category] = []
        file_categories[category].append(file)
    
    return render_template('dashboard.html', files=files, file_categories=file_categories,
                          is_admin=current_user.is_admin, is_guest=current_user.is_guest)

@app.route('/upload', methods=['POST'])
@login_required
def upload_file():
    # Guest tidak boleh upload file
    if current_user.is_guest:
        flash('Guest account cannot upload files', 'danger')
        return redirect(url_for('dashboard'))
        
    if 'file' not in request.files:
        flash('No file part', 'danger')
        return redirect(url_for('dashboard'))
        
    file = request.files['file']
    
    if file.filename == '':
        flash('No file selected', 'danger')
        return redirect(url_for('dashboard'))
        
    if file and allowed_file(file.filename):
        original_filename = secure_filename(file.filename)
        extension = original_filename.rsplit('.', 1)[1].lower() if '.' in original_filename else ''
        
        # Generate a unique filename
        unique_filename = f"{uuid.uuid4().hex}.{extension}"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        
        # Save the file
        file.save(file_path)
        file_size = os.path.getsize(file_path)
        
        # Create file record in database
        new_file = File(
            filename=unique_filename,
            original_filename=original_filename,
            file_type=extension,
            file_size=file_size,
            mime_type=get_mime_type(original_filename),
            user_id=current_user.id
        )
        
        db.session.add(new_file)
        db.session.commit()
        
        # Create initial metadata record
        new_metadata = FileMetadata(file_id=new_file.id)
        db.session.add(new_metadata)
        db.session.commit()
        
        # Process file with AI in the background (this would typically be done asynchronously in production)
        # Process dengan AI - coba-tangkap error
        try:
            logger.info(f"Memulai proses AI untuk file {new_file.id}")
            process_file_with_ai(new_file.id, file_path)
            logger.info(f"Proses AI selesai untuk file {new_file.id}")
        except Exception as e:
            logger.error(f"Error dalam proses AI untuk file {new_file.id}: {str(e)}")
        
        flash('File berhasil diupload!', 'success')
    else:
        flash('File type not allowed', 'danger')
        
    return redirect(url_for('dashboard'))

@app.route('/files/<int:file_id>')
@login_required
def file_details(file_id):
    # Admin dapat melihat semua file, user lain hanya miliknya
    if current_user.is_admin:
        file = File.query.filter_by(id=file_id).first_or_404()
    else:
        file = File.query.filter_by(id=file_id, user_id=current_user.id).first_or_404()
    
    # Update last accessed time
    file.last_accessed = datetime.utcnow()
    db.session.commit()
    
    # Get file preview info
    preview_type, preview_data = get_file_preview(file)
    
    return render_template('file_details.html', file=file, preview_type=preview_type, preview_data=preview_data)

@app.route('/preview/<int:file_id>')
@login_required
def preview_file(file_id):
    file = File.query.filter_by(id=file_id, user_id=current_user.id).first_or_404()
    
    # Set content disposition based on file type
    preview_type, preview_path = get_file_preview(file)
    
    return render_template('preview.html', file=file, preview_type=preview_type, preview_path=preview_path)

@app.route('/download/<int:file_id>')
@login_required
def download_file(file_id):
    file = File.query.filter_by(id=file_id, user_id=current_user.id).first_or_404()
    return send_from_directory(
        app.config['UPLOAD_FOLDER'], 
        file.filename, 
        as_attachment=True,
        download_name=file.original_filename
    )

@app.route('/files/<int:file_id>/raw')
@login_required
def raw_file(file_id):
    file = File.query.filter_by(id=file_id, user_id=current_user.id).first_or_404()
    return send_from_directory(app.config['UPLOAD_FOLDER'], file.filename)

@app.route('/files/<int:file_id>/delete', methods=['POST'])
@login_required
def delete_file(file_id):
    file = File.query.filter_by(id=file_id, user_id=current_user.id).first_or_404()
    
    # Delete the physical file
    try:
        os.remove(os.path.join(app.config['UPLOAD_FOLDER'], file.filename))
    except Exception as e:
        app.logger.error(f"Error deleting file {file.filename}: {str(e)}")
    
    # Delete database records
    db.session.delete(file)  # This will also delete the associated metadata due to cascade
    db.session.commit()
    
    flash('File deleted successfully', 'success')
    return redirect(url_for('dashboard'))

@app.route('/search')
@login_required
def search_files():
    query = request.args.get('q', '')
    
    if not query:
        return redirect(url_for('dashboard'))
    
    # Search in filename, file_meta title, keywords, etc.
    files = File.query.join(FileMetadata).filter(
        File.user_id == current_user.id,
        (
            File.original_filename.ilike(f'%{query}%') |
            FileMetadata.title.ilike(f'%{query}%') |
            FileMetadata.keywords.ilike(f'%{query}%') |
            FileMetadata.extracted_text.ilike(f'%{query}%') |
            FileMetadata.ai_tags.ilike(f'%{query}%')
        )
    ).all()
    
    return render_template('dashboard.html', files=files, search_query=query)

@app.route('/toggle-theme', methods=['POST'])
def toggle_theme():
    theme = request.form.get('theme', 'light')
    response = redirect(request.referrer or url_for('index'))
    response.set_cookie('theme', theme, max_age=31536000)  # Set cookie for 1 year
    return response

# Error handlers
@app.errorhandler(404)
def page_not_found(e):
    return render_template('error.html', error_code=404, error_message='Page not found'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('error.html', error_code=500, error_message='Internal server error'), 500
