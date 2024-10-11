from flask import render_template, request, jsonify
from app import app, db
from models import Workout
from datetime import datetime, timedelta
from sqlalchemy import func

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/workouts', methods=['GET'])
def get_workouts():
    workouts = Workout.query.all()
    return jsonify([workout.to_dict() for workout in workouts])

@app.route('/api/add_workout', methods=['POST'])
def add_workout():
    data = request.json
    new_workout = Workout(
        date=datetime.strptime(data['date'], '%Y-%m-%d').date(),
        duration=data['duration'],
        exercise_type=data['exercise_type']
    )
    db.session.add(new_workout)
    db.session.commit()
    return jsonify(new_workout.to_dict()), 201

@app.route('/api/stats', methods=['GET'])
def get_stats():
    total_workouts = Workout.query.count()
    
    current_streak = 0
    last_workout_date = Workout.query.order_by(Workout.date.desc()).first().date
    current_date = datetime.utcnow().date()
    
    while last_workout_date >= current_date - timedelta(days=current_streak):
        if Workout.query.filter(Workout.date == current_date - timedelta(days=current_streak)).first():
            current_streak += 1
        else:
            break
    
    most_active_day = db.session.query(
        Workout.date,
        func.count(Workout.id).label('count')
    ).group_by(Workout.date).order_by(func.count(Workout.id).desc()).first()

    return jsonify({
        'total_workouts': total_workouts,
        'current_streak': current_streak,
        'most_active_day': most_active_day[0].isoformat() if most_active_day else None
    })
