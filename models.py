from app import db
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256))
    workouts = db.relationship('Workout', backref='user', lazy='dynamic')
    strava_access_token = db.Column(db.String(128))
    strava_refresh_token = db.Column(db.String(128))
    strava_token_expiration = db.Column(db.DateTime)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Workout(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    duration = db.Column(db.Integer, nullable=False)  # Duration in minutes
    exercise_type = db.Column(db.String(100), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    strava_id = db.Column(db.String(128), unique=True)  # Add this line

    def to_dict(self):
        return {
            'id': self.id,
            'date': self.date.isoformat(),
            'duration': self.duration,
            'exercise_type': self.exercise_type,
            'strava_id': self.strava_id  # Add this line
        }
