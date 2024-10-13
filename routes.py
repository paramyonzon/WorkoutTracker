from flask import render_template, jsonify
from app import app
from models import Activity
from strava_utils import fetch_strava_activities, ATHLETE_ID
from data_processing import process_activities
from datetime import datetime, timedelta
import json
import logging

logger = logging.getLogger(__name__)

@app.route('/')
def index():
    return calendar()

@app.route('/calendar')
def calendar():
    activities = Activity.query.all()
    activity_data = {activity.date.isoformat(): activity.activity_level for activity in activities}
    logger.info(f"Rendering calendar with {len(activity_data)} activities")
    return render_template('calendar.html', activity_data=json.dumps(activity_data))

@app.route('/activity_details/<date>')
def activity_details(date):
    try:
        activity_date = datetime.strptime(date, '%Y-%m-%d').date()
        activity = Activity.query.filter_by(date=activity_date).first()
        
        if activity:
            strava_activities = fetch_strava_activities(after=activity_date, before=activity_date + timedelta(days=1))
            activity_names = [a['type'] for a in strava_activities]
            logger.info(f"Fetched {len(activity_names)} activities for {date}")
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
    except Exception as e:
        logger.error(f"Unexpected error in activity_details: {str(e)}")
        return jsonify({'error': 'An unexpected error occurred'}), 500

def fetch_and_process_activities():
    try:
        activities = fetch_strava_activities()
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
                app.db.session.add(new_activity)
        
        app.db.session.commit()
        logger.info(f"Processed and saved {len(processed_activities)} activities")
        return True
    except Exception as e:
        logger.error(f"Error in fetch_and_process_activities: {str(e)}")
        return False

# Fetch activities on application startup
with app.app_context():
    fetch_and_process_activities()
