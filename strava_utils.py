import os
import requests
from datetime import datetime
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

STRAVA_CLIENT_ID = os.environ.get('STRAVA_CLIENT_ID')
STRAVA_CLIENT_SECRET = os.environ.get('STRAVA_CLIENT_SECRET')
ATHLETE_ID = 24481497

logger.debug(f"STRAVA_CLIENT_ID: {'Set' if STRAVA_CLIENT_ID else 'Not set'}")
logger.debug(f"STRAVA_CLIENT_SECRET: {'Set' if STRAVA_CLIENT_SECRET else 'Not set'}")

def refresh_access_token():
    logger.debug("Refreshing access token")
    response = requests.post(
        'https://www.strava.com/oauth/token',
        data={
            'client_id': STRAVA_CLIENT_ID,
            'client_secret': STRAVA_CLIENT_SECRET,
            'grant_type': 'refresh_token',
            'refresh_token': os.environ.get('STRAVA_REFRESH_TOKEN')
        }
    )
    if response.status_code == 200:
        logger.debug("Successfully refreshed access token")
        token_data = response.json()
        os.environ['STRAVA_ACCESS_TOKEN'] = token_data['access_token']
        os.environ['STRAVA_REFRESH_TOKEN'] = token_data['refresh_token']
        return token_data['access_token']
    else:
        logger.error(f"Failed to refresh access token. Status: {response.status_code}, Response: {response.text}")
        return None

def fetch_strava_activities(after=None, before=None):
    logger.debug(f"Fetching Strava activities for athlete {ATHLETE_ID}")
    access_token = os.environ.get('STRAVA_ACCESS_TOKEN')
    if not access_token:
        access_token = refresh_access_token()
        if not access_token:
            logger.error("Failed to obtain access token")
            return []

    headers = {'Authorization': f'Bearer {access_token}'}
    params = {'per_page': 200, 'athlete_id': ATHLETE_ID}
    if after:
        params['after'] = int(after.timestamp())
    if before:
        params['before'] = int(before.timestamp())
    
    response = requests.get(f'https://www.strava.com/api/v3/athlete/activities', headers=headers, params=params)
    if response.status_code == 200:
        activities = response.json()
        logger.debug(f"Successfully fetched {len(activities)} activities")
        return activities
    elif response.status_code == 401:
        logger.warning("Access token expired, refreshing and retrying")
        new_access_token = refresh_access_token()
        if new_access_token:
            return fetch_strava_activities(after, before)
        else:
            logger.error("Failed to refresh access token")
            return []
    else:
        logger.error(f"Failed to fetch activities. Status: {response.status_code}, Response: {response.text}")
        return []
