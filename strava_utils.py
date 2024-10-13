import os
import requests
from urllib.parse import urlencode
from datetime import datetime
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

STRAVA_CLIENT_ID = os.environ.get('STRAVA_CLIENT_ID')
STRAVA_CLIENT_SECRET = os.environ.get('STRAVA_CLIENT_SECRET')
REDIRECT_URI = os.environ.get('REPLIT_DB_URL', '').replace('https://', 'https://').split('.')[0] + '.repl.co/strava_callback'
ATHLETE_ID = 24481497

logger.info(f"STRAVA_CLIENT_ID: {'Set' if STRAVA_CLIENT_ID else 'Not set'}")
logger.info(f"STRAVA_CLIENT_SECRET: {'Set' if STRAVA_CLIENT_SECRET else 'Not set'}")
logger.info(f"REDIRECT_URI: {REDIRECT_URI}")

def get_strava_auth_url():
    params = {
        'client_id': STRAVA_CLIENT_ID,
        'redirect_uri': REDIRECT_URI,
        'response_type': 'code',
        'scope': 'activity:read_all',
        'state': str(ATHLETE_ID)
    }
    auth_url = f"https://www.strava.com/oauth/authorize?{urlencode(params)}"
    logger.info(f"Generated Strava auth URL: {auth_url}")
    return auth_url

def exchange_code_for_token(code):
    logger.info(f"Exchanging code for token: {code}")
    response = requests.post(
        'https://www.strava.com/oauth/token',
        data={
            'client_id': STRAVA_CLIENT_ID,
            'client_secret': STRAVA_CLIENT_SECRET,
            'code': code,
            'grant_type': 'authorization_code'
        }
    )
    if response.status_code == 200:
        logger.info("Successfully exchanged code for token")
        return response.json()
    else:
        logger.error(f"Failed to exchange code for token. Status: {response.status_code}, Response: {response.text}")
        return None

def refresh_access_token(refresh_token):
    logger.info("Refreshing access token")
    response = requests.post(
        'https://www.strava.com/oauth/token',
        data={
            'client_id': STRAVA_CLIENT_ID,
            'client_secret': STRAVA_CLIENT_SECRET,
            'refresh_token': refresh_token,
            'grant_type': 'refresh_token'
        }
    )
    if response.status_code == 200:
        logger.info("Successfully refreshed access token")
        return response.json()
    else:
        logger.error(f"Failed to refresh access token. Status: {response.status_code}, Response: {response.text}")
        return None

def fetch_strava_activities(access_token, after=None, before=None):
    logger.info(f"Fetching Strava activities for athlete {ATHLETE_ID}")
    headers = {'Authorization': f'Bearer {access_token}'}
    params = {'per_page': 200}
    if after:
        params['after'] = int(after.timestamp())
    if before:
        params['before'] = int(before.timestamp())
    
    response = requests.get(f'https://www.strava.com/api/v3/athletes/{ATHLETE_ID}/activities', headers=headers, params=params)
    if response.status_code == 200:
        logger.info(f"Successfully fetched {len(response.json())} activities")
        return response.json()
    else:
        logger.error(f"Failed to fetch activities. Status: {response.status_code}, Response: {response.text}")
        return []
