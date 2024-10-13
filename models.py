from app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    strava_access_token = db.Column(db.String(128))
    strava_refresh_token = db.Column(db.String(128))
    strava_token_expiry = db.Column(db.DateTime)

class Activity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    activity_level = db.Column(db.Float, nullable=False)
