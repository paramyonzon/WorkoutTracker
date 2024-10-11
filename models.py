from app import db
from datetime import datetime

class Workout(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    duration = db.Column(db.Integer, nullable=False)  # Duration in minutes
    exercise_type = db.Column(db.String(100), nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'date': self.date.isoformat(),
            'duration': self.duration,
            'exercise_type': self.exercise_type
        }
