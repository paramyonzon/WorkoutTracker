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

# Set up logging
logging.basicConfig(level=logging.INFO)
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
            return redirect(url_for('index'))
        flash('Invalid username or password')
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
    client = Client()
    try:
        client_id = os.environ['STRAVA_CLIENT_ID']
        client_secret = os.environ['STRAVA_CLIENT_SECRET']
        
        # Ensure client_id is an integer
        try:
            client_id = int(client_id)
        except ValueError:
            logger.error(f"STRAVA_CLIENT_ID is not a valid integer: {client_id}")
            flash('Invalid Strava client ID. Please contact the administrator.', 'error')
            return redirect(url_for('index'))
        
    except KeyError as e:
        logger.error(f"Missing Strava credentials: {str(e)}")
        flash('Missing Strava credentials. Please contact the administrator.', 'error')
        return redirect(url_for('index'))

    redirect_uri = url_for('strava_callback', _external=True, _scheme='https')
    authorize_url = client.authorization_url(
        client_id=client_id,
        redirect_uri=redirect_uri,
        scope=['read_all', 'activity:read_all']
    )
    logger.info(f"Strava authorization URL: {authorize_url}")
    return redirect(authorize_url)

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
        # Check if token is expired and refresh if necessary
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
    except Exception as e:
        logger.error(f"Error importing Strava activities: {str(e)}")
        flash('Error importing Strava activities. Please try again later.', 'error')
    
    return redirect(url_for('index'))

# Add other existing routes here...
