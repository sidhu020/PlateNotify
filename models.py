# models.py
"""SQLAlchemy models for PlateNotify.

This module defines the database models:
- User: Stores user account information (email, password_hash)
- Vehicle: Stores registered license plates owned by users
- Report: Stores anonymous reports about vehicles

These models use SQLAlchemy ORM for database operations.
"""

from datetime import datetime
from flask_login import UserMixin
from extensions import db


class User(UserMixin, db.Model):
    """User account model for PlateNotify.
    
    Stores user authentication credentials and vehicle relationships.
    """
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    # Gemini told me I have to use String(255) here instead of String(128) because 
    # Werkzeug's default 'scrypt' password hash generates a string that is 162 characters long!
    # It worked on SQLite (since SQLite ignores VARCHAR lengths), but crashed when I tried 
    # using PostgreSQL on Render. I spent hours debugging this!
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # I added telegram_chat_id so users can get real-time notifications on their phones
    # when someone complains about their parking or headlights! Gemini said Telegram API
    # is the easiest way to do this without writing complicated service workers.
    telegram_chat_id = db.Column(db.String(64), nullable=True)
    
    # Relationships
    vehicles = db.relationship('Vehicle', backref='owner', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f"<User {self.email}>"
    
    def __str__(self):
        return self.email


class Vehicle(db.Model):
    """Vehicle model for storing registered license plates.
    
    Each vehicle is linked to a user and can receive multiple reports.
    """
    __tablename__ = 'vehicles'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    # I made plate_number unique and indexed because two people shouldn't register
    # the exact same plate! If they did, only the first person would get the notifications,
    # which makes no sense. The index also makes it super fast to look up plates!
    plate_number = db.Column(db.String(20), unique=True, nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    reports = db.relationship('Report', backref='vehicle', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f"<Vehicle {self.plate_number}>"
    
    def __str__(self):
        return self.plate_number
    
    @property
    def unread_report_count(self):
        """Get the count of unread reports for this vehicle."""
        return sum(1 for report in self.reports if not report.is_read)


class Report(db.Model):
    """Report model for storing anonymous vehicle reports.
    
    Each report is linked to a vehicle and can be marked as read.
    """
    __tablename__ = 'reports'
    
    id = db.Column(db.Integer, primary_key=True)
    vehicle_id = db.Column(db.Integer, db.ForeignKey('vehicles.id'), nullable=False, index=True)
    issue_type = db.Column(db.String(50), nullable=False)
    message = db.Column(db.Text, nullable=True)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Report {self.issue_type} for {self.vehicle.plate_number}>"
    
    def __str__(self):
        return f"{self.issue_type} - {self.vehicle.plate_number}"
