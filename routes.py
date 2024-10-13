from flask import render_template, request, jsonify, redirect, url_for, flash, session
from flask_login import login_user, login_required, logout_user, current_user
from app import app, db
from models import User, Workout
from datetime import datetime, timedelta
from sqlalchemy import func
import calendar
from stravalib.client import Client
import os
import logging
import requests

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            logger.info(f"User {username} logged in successfully")
            return redirect(url_for('index'))
        else:
            logger.warning(f"Failed login attempt for user {username}")
            flash('Invalid username or password', 'error')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        if User.query.filter_by(username=username).first():
            flash('Username already exists')
        elif User.query.filter_by(email=email).first():
            flash('Email already exists')
        else:
            user = User(username=username, email=email)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            flash('Registration successful. Please log in.')
            return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/')
@login_required
def index():
    strava_connected = bool(current_user.strava_access_token)
    return render_template('index.html', strava_connected=strava_connected)

@app.route('/strava_auth')
@login_required
def strava_auth():
    try:
        client_id = os.environ['STRAVA_CLIENT_ID']
        client_secret = os.environ['STRAVA_CLIENT_SECRET']
        logger.info(f"Strava credentials loaded: Client ID: {client_id}, Client Secret: {'*' * len(client_secret)}")
        
        try:
            client_id = int(client_id)
        except ValueError:
            logger.error(f"STRAVA_CLIENT_ID is not a valid integer: {client_id}")
            flash('Invalid Strava client ID. Please contact the administrator.', 'error')
            return redirect(url_for('index'))
        
        redirect_uri = url_for('strava_callback', _external=True, _scheme='https')
        logger.info(f"Redirect URI: {redirect_uri}")
        
        client = Client()
        authorize_url = client.authorization_url(
            client_id=client_id,
            redirect_uri=redirect_uri,
            scope=['read_all', 'activity:read_all']
        )
        logger.info(f"Strava authorization URL: {authorize_url}")
        return redirect(authorize_url)
    except KeyError as e:
        logger.error(f"Missing Strava credentials: {str(e)}")
        flash('Missing Strava credentials. Please contact the administrator.', 'error')
        return redirect(url_for('index'))
    except Exception as e:
        logger.error(f"Error in Strava authorization: {str(e)}")
        flash('Error initiating Strava authorization. Please try again.', 'error')
        return redirect(url_for('index'))

@app.route('/strava_callback')
@login_required
def strava_callback():
    try:
        code = request.args.get('code')
        client = Client()
        token_response = client.exchange_code_for_token(
            client_id=int(os.environ['STRAVA_CLIENT_ID']),
            client_secret=os.environ['STRAVA_CLIENT_SECRET'],
            code=code
        )
        
        current_user.strava_access_token = token_response['access_token']
        current_user.strava_refresh_token = token_response['refresh_token']
        current_user.strava_token_expiration = datetime.fromtimestamp(token_response['expires_at'])
        db.session.commit()
        
        flash('Strava account connected successfully!', 'success')
        logger.info(f"Strava account connected for user {current_user.id}")
    except requests.exceptions.RequestException as e:
        logger.error(f"Network error in Strava callback: {str(e)}")
        flash('Network error connecting Strava account. Please try again.', 'error')
    except Exception as e:
        logger.error(f"Error in Strava callback: {str(e)}")
        flash('Error connecting Strava account. Please try again.', 'error')
    
    return redirect(url_for('index'))

@app.route('/import_strava_activities')
@login_required
def import_strava_activities():
    if not current_user.strava_access_token:
        flash('Please connect your Strava account first.', 'warning')
        return redirect(url_for('index'))
    
    client = Client(access_token=current_user.strava_access_token)
    
    try:
        if datetime.utcnow() > current_user.strava_token_expiration:
            refresh_response = client.refresh_access_token(
                client_id=int(os.environ['STRAVA_CLIENT_ID']),
                client_secret=os.environ['STRAVA_CLIENT_SECRET'],
                refresh_token=current_user.strava_refresh_token
            )
            current_user.strava_access_token = refresh_response['access_token']
            current_user.strava_refresh_token = refresh_response['refresh_token']
            current_user.strava_token_expiration = datetime.fromtimestamp(refresh_response['expires_at'])
            db.session.commit()
            client = Client(access_token=current_user.strava_access_token)
        
        activities = client.get_activities(after=datetime.utcnow() - timedelta(days=30))
        imported_count = 0
        
        for activity in activities:
            existing_workout = Workout.query.filter_by(strava_id=str(activity.id)).first()
            if not existing_workout:
                new_workout = Workout(
                    date=activity.start_date.date(),
                    duration=int(activity.moving_time.total_seconds() / 60),
                    exercise_type=activity.type,
                    user_id=current_user.id,
                    strava_id=str(activity.id)
                )
                db.session.add(new_workout)
                imported_count += 1
        
        db.session.commit()
        flash(f'Successfully imported {imported_count} new activities from Strava.', 'success')
        logger.info(f"Imported {imported_count} activities for user {current_user.id}")
    except requests.exceptions.RequestException as e:
        logger.error(f"Network error importing Strava activities: {str(e)}")
        flash('Network error importing Strava activities. Please try again later.', 'error')
    except Exception as e:
        logger.error(f"Error importing Strava activities: {str(e)}")
        flash('Error importing Strava activities. Please try again later.', 'error')
    
    return redirect(url_for('index'))

@app.route('/api/workouts')
@login_required
def get_workouts():
    workouts = Workout.query.filter_by(user_id=current_user.id).all()
    return jsonify([workout.to_dict() for workout in workouts])

@app.route('/api/stats')
@login_required
def get_stats():
    total_workouts = Workout.query.filter_by(user_id=current_user.id).count()
    
    workouts = Workout.query.filter_by(user_id=current_user.id).order_by(Workout.date.desc()).all()
    current_streak = 0
    for i, workout in enumerate(workouts):
        if i == 0 or (workouts[i-1].date - workout.date).days == 1:
            current_streak += 1
        else:
            break
    
    most_active_day = db.session.query(
        Workout.date,
        func.sum(Workout.duration).label('total_duration')
    ).filter_by(user_id=current_user.id).group_by(Workout.date).order_by(func.sum(Workout.duration).desc()).first()
    
    return jsonify({
        'total_workouts': total_workouts,
        'current_streak': current_streak,
        'most_active_day': most_active_day.date.isoformat() if most_active_day else None
    })

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
    return jsonify(new_workout.to_dict())

@app.route('/api/workout_progress')
@login_required
def workout_progress():
    workouts = Workout.query.filter_by(user_id=current_user.id).order_by(Workout.date).all()
    progress_data = []
    total_duration = 0
    for workout in workouts:
        total_duration += workout.duration
        progress_data.append({
            'date': workout.date.isoformat(),
            'total_duration': total_duration
        })
    return jsonify(progress_data)

@app.route('/api/weekly_workouts')
@login_required
def weekly_workouts():
    end_date = datetime.now().date()
    start_date = end_date - timedelta(weeks=12)
    workouts = Workout.query.filter(
        Workout.user_id == current_user.id,
        Workout.date >= start_date,
        Workout.date <= end_date
    ).order_by(Workout.date).all()
    
    weekly_data = {}
    for workout in workouts:
        week = workout.date.isocalendar()[1]
        if week not in weekly_data:
            weekly_data[week] = 0
        weekly_data[week] += workout.duration
    
    return jsonify([{'week': week, 'total_duration': duration} for week, duration in weekly_data.items()])

@app.route('/api/exercise_type_distribution')
@login_required
def exercise_type_distribution():
    distribution = db.session.query(
        Workout.exercise_type,
        func.count(Workout.id).label('count')
    ).filter_by(user_id=current_user.id).group_by(Workout.exercise_type).all()
    
    return jsonify({exercise_type: count for exercise_type, count in distribution})