from flask import render_template, request, redirect, url_for, flash, jsonify
from app import app, db
from models import User, Activity
from strava_utils import get_strava_auth_url, exchange_code_for_token, refresh_access_token, fetch_strava_activities, ATHLETE_ID
from data_processing import process_activities
from datetime import datetime, timedelta
import json
import logging

logger = logging.getLogger(__name__)

@app.route('/')
def index():
    return redirect(url_for('calendar'))

@app.route('/calendar')
def calendar():
    user = User.query.first()
    if not user or not user.strava_access_token:
        logger.warning("No user or Strava access token found")
        return render_template('calendar.html', activity_data=json.dumps({}))
    
    activities = Activity.query.all()
    activity_data = {activity.date.isoformat(): activity.activity_level for activity in activities}
    logger.info(f"Rendering calendar with {len(activity_data)} activities")
    return render_template('calendar.html', activity_data=json.dumps(activity_data))

@app.route('/strava_auth')
def strava_auth():
    auth_url = get_strava_auth_url()
    logger.info(f"Redirecting to Strava auth URL: {auth_url}")
    return redirect(auth_url)

@app.route('/strava_callback')
def strava_callback():
    error = request.args.get('error')
    if error:
        logger.error(f"Strava authentication error: {error}")
        flash(f'Strava authentication failed: {error}', 'error')
        return redirect(url_for('calendar'))

    code = request.args.get('code')
    logger.info(f"Received Strava callback with code: {code}")
    token_data = exchange_code_for_token(code)
    
    if token_data:
        user = User.query.first()
        if not user:
            user = User()
            db.session.add(user)
            logger.info("Created new user")
        
        user.strava_access_token = token_data['access_token']
        user.strava_refresh_token = token_data['refresh_token']
        user.strava_token_expiry = datetime.fromtimestamp(token_data['expires_at'])
        db.session.commit()
        logger.info("Updated user with new Strava tokens")
        
        fetch_and_process_activities()
        flash('Strava account connected successfully!', 'success')
    else:
        logger.error("Failed to connect Strava account")
        flash('Failed to connect Strava account. Please try again.', 'error')
    
    return redirect(url_for('calendar'))

@app.route('/refresh_activities')
def refresh_activities():
    result = fetch_and_process_activities()
    if result:
        flash('Activities refreshed successfully!', 'success')
    else:
        flash('Failed to refresh activities. Please try reconnecting your Strava account.', 'error')
    return redirect(url_for('calendar'))

@app.route('/activity_details/<date>')
def activity_details(date):
    try:
        activity_date = datetime.strptime(date, '%Y-%m-%d').date()
        activity = Activity.query.filter_by(date=activity_date).first()
        
        if activity:
            user = User.query.first()
            if user and user.strava_access_token:
                strava_activities = fetch_strava_activities(user.strava_access_token, after=activity_date, before=activity_date + timedelta(days=1))
                activity_names = [a['type'] for a in strava_activities]
                logger.info(f"Fetched {len(activity_names)} activities for {date}")
            else:
                activity_names = []
                logger.warning("No user or Strava access token found when fetching activity details")
            return jsonify({
                'activity_level': activity.activity_level,
                'activities': activity_names
            })
        else:
            logger.info(f"No activity found for {date}")
            return jsonify({
                'activity_level': 0,
                'activities': []
            })
    except ValueError:
        logger.error(f"Invalid date format: {date}")
        return jsonify({'error': 'Invalid date format'}), 400

def fetch_and_process_activities():
    user = User.query.first()
    if not user:
        logger.error("No user found in the database")
        return False

    if user.strava_token_expiry and user.strava_token_expiry <= datetime.now():
        logger.info("Refreshing expired Strava token")
        token_data = refresh_access_token(user.strava_refresh_token)
        if token_data:
            user.strava_access_token = token_data['access_token']
            user.strava_refresh_token = token_data['refresh_token']
            user.strava_token_expiry = datetime.fromtimestamp(token_data['expires_at'])
            db.session.commit()
            logger.info("Successfully refreshed Strava token")
        else:
            logger.error("Failed to refresh Strava token")
            return False
    
    activities = fetch_strava_activities(user.strava_access_token)
    if not activities:
        logger.error("Failed to fetch Strava activities")
        return False

    processed_activities = process_activities(activities)
    
    for date, activity_level in processed_activities.items():
        existing_activity = Activity.query.filter_by(date=date).first()
        if existing_activity:
            existing_activity.activity_level = activity_level
        else:
            new_activity = Activity(date=date, activity_level=activity_level)
            db.session.add(new_activity)
    
    db.session.commit()
    logger.info(f"Processed and saved {len(processed_activities)} activities")
    return True
