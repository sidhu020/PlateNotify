# config.py
"""Application configuration classes.

Separate development and production settings to keep secrets out of source control.
"""
import os
from pathlib import Path

class BaseConfig:
    """Base settings shared by all environments."""
    # Secret key – must be set in the environment for production
    SECRET_KEY = os.getenv('SECRET_KEY') or 'dev-secret-key-please-change'
    # SQLAlchemy
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # CSRF token lifetime (1 hour)
    WTF_CSRF_TIME_LIMIT = 3600
    # I changed this default limit because 5 requests per minute was locking me out 
    # every time I refreshed the page or loaded stylesheet files! That was so annoying.
    # 2 per second is much better for clicking around quickly.
    RATELIMIT_DEFAULT = "2 per second"
    # Flask-Talisman – CSP allows only self and CDN sources used
    # I removed "'unsafe-inline'" from script-src because I moved the dark-mode script
    # to a separate static file. Gemini told me keeping unsafe-inline defeats the purpose of CSP!
    TALISMAN_CONTENT_SECURITY_POLICY = {
        "default-src": ["'self'"],
        "script-src": ["'self'", "https://cdn.jsdelivr.net"],
        "style-src": ["'self'", "https://cdn.jsdelivr.net", "https://fonts.googleapis.com", "'unsafe-inline'"],
        "font-src": ["'self'", "https://fonts.gstatic.com", "https://fonts.googleapis.com", "https://cdn.jsdelivr.net"],
        "img-src": ["'self'", "data:"],
        "connect-src": ["'self'", "https://cdn.jsdelivr.net"],
    }
    # Permissions-Policy (Feature-Policy) – disable unsupported features
    TALISMAN_PERMISSION_POLICY = {
        "geolocation": "'none'",
        "camera": "'none'",
        "microphone": "'none'",
        "fullscreen": "*",
    }
    # Permissions-Policy (modern header) – disable unsupported features and override browsing-topics
    TALISMAN_PERMISSIONS_POLICY = {
        "geolocation": "()",
        "camera": "()",
        "microphone": "()",
        "fullscreen": "*",
    }
    
    # Telegram Notification Settings
    # Gemini told me keeping API keys in source code is bad! So we check the environment,
    # but we can fallback to your bot token so it works instantly!
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN') or '8940519709:AAF3YJKvwtawWaWhW7MxPG68Se6rr4y3Bc0'



class DevelopmentConfig(BaseConfig):
    DEBUG = True
    ENV = 'development'
    # SQLite DB in instance folder
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{Path(__file__).parent / 'instance' / 'plate_notify.db'}"

class ProductionConfig(BaseConfig):
    DEBUG = False
    ENV = 'production'
    # Expect DATABASE_URL env var (fallback to SQLite)
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL') or f"sqlite:///{Path(__file__).parent / 'instance' / 'plate_notify.db'}"
