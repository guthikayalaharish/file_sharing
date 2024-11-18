from itsdangerous import URLSafeTimedSerializer
from flask_mail import Message
from . import mail
from functools import wraps
from flask import request, jsonify
from .models import User

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('x-access-token')
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401
        try:
            user = User.query.filter_by(email=token).first()
            if not user:
                raise ValueError()
        except:
            return jsonify({'message': 'Invalid token!'}), 401
        return f(user, *args, **kwargs)
    return decorated

def generate_secure_url(filename):
    s = URLSafeTimedSerializer('SECRET_KEY')
    return f'/uploads/{filename}?token={s.dumps(filename)}'

def send_verification_email(email):
    msg = Message('Verify Your Email', recipients=[email])
    msg.body = f'Click here to verify your email: /verify-email/{email}'
    mail.send(msg)
