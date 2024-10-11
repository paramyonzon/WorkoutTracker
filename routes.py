from flask import render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_user, login_required, logout_user, current_user
from app import app, db
from models import User, Workout
from datetime import datetime, timedelta
from sqlalchemy import func
import calendar

@app.route('/')
@login_required
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        if user:
            flash('Username already exists')
            return redirect(url_for('register'))
        
        user = User.query.filter_by(email=email).first()
        if user:
            flash('Email already exists')
            return redirect(url_for('register'))
        
        new_user = User(username=username, email=email)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        
        flash('Registration successful')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/api/workouts', methods=['GET'])
@login_required
def get_workouts():
    workouts = current_user.workouts.all()
    return jsonify([workout.to_dict() for workout in workouts])

@app.route('/api/add_workout', methods=['POST'])
@login_required
def add_workout():
    data = request.json
    new_workout = Workout(
        date=datetime.strptime(data['date'], '%Y-%m-%d').date(),
        duration=data['duration'],
        exercise_type=data['exercise_type'],
        user_id=current_user.id
    )
    db.session.add(new_workout)
    db.session.commit()
    return jsonify(new_workout.to_dict()), 201

@app.route('/api/stats', methods=['GET'])
@login_required
def get_stats():
    total_workouts = current_user.workouts.count()
    
    current_streak = 0
    last_workout = current_user.workouts.order_by(Workout.date.desc()).first()
    
    if last_workout:
        last_workout_date = last_workout.date
        current_date = datetime.utcnow().date()
        
        while last_workout_date >= current_date - timedelta(days=current_streak):
            if current_user.workouts.filter(Workout.date == current_date - timedelta(days=current_streak)).first():
                current_streak += 1
            else:
                break
    
    most_active_day = db.session.query(
        Workout.date,
        func.count(Workout.id).label('count')
    ).filter(Workout.user_id == current_user.id).group_by(Workout.date).order_by(func.count(Workout.id).desc()).first()

    return jsonify({
        'total_workouts': total_workouts,
        'current_streak': current_streak,
        'most_active_day': most_active_day[0].isoformat() if most_active_day else None
    })

@app.route('/api/workout_progress', methods=['GET'])
@login_required
def get_workout_progress():
    workouts = current_user.workouts.order_by(Workout.date).all()
    progress_data = []
    total_duration = 0
    for workout in workouts:
        total_duration += workout.duration
        progress_data.append({
            'date': workout.date.isoformat(),
            'total_duration': total_duration
        })
    return jsonify(progress_data)

@app.route('/api/weekly_workouts', methods=['GET'])
@login_required
def get_weekly_workouts():
    end_date = datetime.utcnow().date()
    start_date = end_date - timedelta(days=365)  # Last year's data
    
    weekly_workouts = db.session.query(
        func.date_trunc('week', Workout.date).label('week'),
        func.sum(Workout.duration).label('total_duration')
    ).filter(
        Workout.user_id == current_user.id,
        Workout.date >= start_date,
        Workout.date <= end_date
    ).group_by(func.date_trunc('week', Workout.date)).order_by(func.date_trunc('week', Workout.date)).all()
    
    return jsonify([
        {
            'week': week.strftime('%Y-%m-%d'),
            'total_duration': total_duration
        } for week, total_duration in weekly_workouts
    ])

@app.route('/api/exercise_type_distribution', methods=['GET'])
@login_required
def get_exercise_type_distribution():
    distribution = db.session.query(
        Workout.exercise_type,
        func.count(Workout.id).label('count')
    ).filter(Workout.user_id == current_user.id).group_by(Workout.exercise_type).all()
    
    return jsonify({exercise_type: count for exercise_type, count in distribution})
