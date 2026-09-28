import os
import secrets
from flask import Flask
from dotenv import load_dotenv
from flask_wtf.csrf import CSRFProtect

load_dotenv()

csrf = CSRFProtect()


def create_app():
    app = Flask(__name__, template_folder="../templates", static_folder="../static")
    app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY') or secrets.token_hex(32)
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    app.config['SESSION_COOKIE_SECURE'] = os.getenv('SESSION_COOKIE_SECURE', 'false').lower() == 'true'
    app.config['JAVA_API_URL'] = os.getenv('JAVA_API_URL', 'http://localhost:8080')
    csrf.init_app(app)
    from .routes import main_bp
    app.register_blueprint(main_bp)
    return app
