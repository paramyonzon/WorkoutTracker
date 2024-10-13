from flask import render_template, request, redirect, url_for, flash, jsonify
from app import app, db
from models import User, Activity
from strava_utils import get_strava_auth_url, exchange_code_for_token, refresh_access_token, fetch_strava_activities, ATHLETE_ID
from data_processing import process_activities
from datetime import datetime, timedelta
import json

@app.route('/')
def index():
    return redirect(url_for('calendar'))

@app.route('/calendar')
def calendar():
    user = User.query.first()
    if not user or not user.strava_access_token:
        return render_template('calendar.html', activity_data=json.dumps({}))
    
    activities = Activity.query.all()
    activity_data = {activity.date.isoformat(): activity.activity_level for activity in activities}
    return render_template('calendar.html', activity_data=json.dumps(activity_data))

@app.route('/strava_auth')
def strava_auth():
    auth_url = get_strava_auth_url()
    return redirect(auth_url)

@app.route('/strava_callback')
def strava_callback():
    code = request.args.get('code')
    token_data = exchange_code_for_token(code)
    
    if token_data:
        user = User.query.first()
        if not user:
            user = User()
            db.session.add(user)
        
        user.strava_access_token = token_data['access_token']
        user.strava_refresh_token = token_data['refresh_token']
        user.strava_token_expiry = datetime.fromtimestamp(token_data['expires_at'])
        db.session.commit()
        
        fetch_and_process_activities()
        flash('Strava account connected successfully!', 'success')
    else:
        flash('Failed to connect Strava account.', 'error')
    
    return redirect(url_for('calendar'))

@app.route('/refresh_activities')
def refresh_activities():
    fetch_and_process_activities()
    flash('Activities refreshed successfully!', 'success')
    return redirect(url_for('calendar'))

@app.route('/activity_details/<date>')
def activity_details(date):
    try:
        activity_date = datetime.strptime(date, '%Y-%m-%d').date()
        activity = Activity.query.filter_by(date=activity_date).first()
        
        if activity:
            user = User.query.first()
            strava_activities = fetch_strava_activities(user.strava_access_token, after=activity_date, before=activity_date + timedelta(days=1))
            activity_names = [a['type'] for a in strava_activities]
            return jsonify({
                'activity_level': activity.activity_level,
                'activities': activity_names
            })
        else:
            return jsonify({
                'activity_level': 0,
                'activities': []
            })
    except ValueError:
        return jsonify({'error': 'Invalid date format'}), 400

def fetch_and_process_activities():
    user = User.query.first()
    if not user:
        return

    if user.strava_token_expiry and user.strava_token_expiry <= datetime.now():
        token_data = refresh_access_token(user.strava_refresh_token)
        if token_data:
            user.strava_access_token = token_data['access_token']
            user.strava_refresh_token = token_data['refresh_token']
            user.strava_token_expiry = datetime.fromtimestamp(token_data['expires_at'])
            db.session.commit()
        else:
            flash('Failed to refresh Strava token.', 'error')
            return
    
    activities = fetch_strava_activities(user.strava_access_token)
    processed_activities = process_activities(activities)
    
    for date, activity_level in processed_activities.items():
        existing_activity = Activity.query.filter_by(date=date).first()
        if existing_activity:
            existing_activity.activity_level = activity_level
        else:
            new_activity = Activity(date=date, activity_level=activity_level)
            db.session.add(new_activity)
    
    db.session.commit()
