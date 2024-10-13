from flask import render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_user, login_required, logout_user, current_user
from app import app, db, login_manager
from models import User, Activity
from strava_utils import get_strava_auth_url, exchange_code_for_token, refresh_access_token, fetch_strava_activities
from data_processing import process_activities
from sqlalchemy.exc import IntegrityError
from datetime import datetime, timedelta
import json

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        user = User(username=username, email=email)
        user.set_password(password)
        
        try:
            db.session.add(user)
            db.session.commit()
            flash('Registration successful. Please log in.', 'success')
            return redirect(url_for('login'))
        except IntegrityError:
            db.session.rollback()
            flash('Username or email already exists.', 'error')
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('calendar'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/calendar')
@login_required
def calendar():
    activities = Activity.query.filter_by(user_id=current_user.id).all()
    activity_data = {activity.date.isoformat(): activity.activity_level for activity in activities}
    return render_template('calendar.html', activity_data=json.dumps(activity_data))

@app.route('/strava_auth')
@login_required
def strava_auth():
    auth_url = get_strava_auth_url()
    return redirect(auth_url)

@app.route('/strava_callback')
@login_required
def strava_callback():
    code = request.args.get('code')
    token_data = exchange_code_for_token(code)
    
    if token_data:
        current_user.strava_access_token = token_data['access_token']
        current_user.strava_refresh_token = token_data['refresh_token']
        current_user.strava_token_expiry = datetime.fromtimestamp(token_data['expires_at'])
        db.session.commit()
        
        fetch_and_process_activities()
        flash('Strava account connected successfully!', 'success')
    else:
        flash('Failed to connect Strava account.', 'error')
    
    return redirect(url_for('calendar'))

@app.route('/refresh_activities')
@login_required
def refresh_activities():
    fetch_and_process_activities()
    flash('Activities refreshed successfully!', 'success')
    return redirect(url_for('calendar'))

@app.route('/activity_details/<date>')
@login_required
def activity_details(date):
    activity = Activity.query.filter_by(user_id=current_user.id, date=date).first()
    if activity:
        # Fetch Strava activities for the given date
        strava_activities = fetch_strava_activities(current_user.strava_access_token, after=activity.date, before=activity.date + timedelta(days=1))
        activity_names = [a['type'] for a in strava_activities]
        return jsonify({
            'activity_level': activity.activity_level,
            'activities': activity_names
        })
    return jsonify({'error': 'No activity found for this date'}), 404

def fetch_and_process_activities():
    if current_user.strava_token_expiry and current_user.strava_token_expiry <= datetime.now():
        token_data = refresh_access_token(current_user.strava_refresh_token)
        if token_data:
            current_user.strava_access_token = token_data['access_token']
            current_user.strava_refresh_token = token_data['refresh_token']
            current_user.strava_token_expiry = datetime.fromtimestamp(token_data['expires_at'])
            db.session.commit()
        else:
            flash('Failed to refresh Strava token.', 'error')
            return
    
    activities = fetch_strava_activities(current_user.strava_access_token)
    processed_activities = process_activities(activities)
    
    for date, activity_level in processed_activities.items():
        existing_activity = Activity.query.filter_by(user_id=current_user.id, date=date).first()
        if existing_activity:
            existing_activity.activity_level = activity_level
        else:
            new_activity = Activity(user_id=current_user.id, date=date, activity_level=activity_level)
            db.session.add(new_activity)
    
    db.session.commit()
