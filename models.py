from app import db
from datetime import datetime

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    strava_access_token = db.Column(db.String(128))
    strava_refresh_token = db.Column(db.String(128))
    strava_token_expiry = db.Column(db.DateTime)

class Activity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    activity_level = db.Column(db.Float, nullable=False)
