from flask import Blueprint, request, jsonify, send_from_directory, url_for
from werkzeug.utils import secure_filename
from .models import db, User, File
from .utils import token_required, generate_secure_url, send_verification_email
import os

main = Blueprint('main', __name__)

ALLOWED_EXTENSIONS = {'pptx', 'docx', 'xlsx'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@main.route('/signup', methods=['POST'])
def signup():
    data = request.json
    hashed_password = bcrypt.generate_password_hash(data['password']).decode('utf-8')
    user = User(email=data['email'], password=hashed_password, user_type='client')
    db.session.add(user)
    db.session.commit()
    send_verification_email(data['email'])
    return jsonify({'message': 'Signup successful! Verify your email.'})

@main.route('/verify-email/<email>', methods=['GET'])
def verify_email(email):
    user = User.query.filter_by(email=email).first()
    if user:
        user.is_verified = True
        db.session.commit()
        return jsonify({'message': 'Email verified!'})
    return jsonify({'message': 'Invalid email.'})

@main.route('/login', methods=['POST'])
def login():
    data = request.json
    user = User.query.filter_by(email=data['email']).first()
    if user and bcrypt.check_password_hash(user.password, data['password']):
        return jsonify({'message': 'Login successful!', 'user_type': user.user_type})
    return jsonify({'message': 'Invalid credentials!'})

@main.route('/upload', methods=['POST'])
@token_required
def upload_file(user):
    if user.user_type != 'ops':
        return jsonify({'message': 'Only Ops User can upload files.'}), 403

    if 'file' not in request.files:
        return jsonify({'message': 'No file provided!'}), 400

    file = request.files['file']
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join('uploads', filename))
        new_file = File(filename=filename, uploader_id=user.id)
        db.session.add(new_file)
        db.session.commit()
        return jsonify({'message': 'File uploaded successfully!'})
    return jsonify({'message': 'Invalid file type!'}), 400

@main.route('/download-file/<int:file_id>', methods=['GET'])
@token_required
def download_file(user, file_id):
    file = File.query.get(file_id)
    if not file:
        return jsonify({'message': 'File not found!'}), 404

    if user.user_type != 'client':
        return jsonify({'message': 'Access denied!'}), 403

    secure_url = generate_secure_url(file.filename)
    return jsonify({'download-link': secure_url, 'message': 'success'})

@main.route('/list-files', methods=['GET'])
@token_required
def list_files(user):
    if user.user_type != 'client':
        return jsonify({'message': 'Access denied!'}), 403

    files = File.query.all()
    return jsonify({'files': [{'id': f.id, 'filename': f.filename} for f in files]})
