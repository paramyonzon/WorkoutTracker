import os
import requests
from urllib.parse import urlencode
from datetime import datetime

STRAVA_CLIENT_ID = os.environ.get('STRAVA_CLIENT_ID')
STRAVA_CLIENT_SECRET = os.environ.get('STRAVA_CLIENT_SECRET')
REDIRECT_URI = os.environ.get('REPLIT_DB_URL', '').replace('https://', 'https://').split('.')[0] + '.repl.co/strava_callback'

def get_strava_auth_url():
    params = {
        'client_id': STRAVA_CLIENT_ID,
        'redirect_uri': REDIRECT_URI,
        'response_type': 'code',
        'scope': 'activity:read_all'
    }
    return f"https://www.strava.com/oauth/authorize?{urlencode(params)}"

def exchange_code_for_token(code):
    response = requests.post(
        'https://www.strava.com/oauth/token',
        data={
            'client_id': STRAVA_CLIENT_ID,
            'client_secret': STRAVA_CLIENT_SECRET,
            'code': code,
            'grant_type': 'authorization_code'
        }
    )
    return response.json() if response.status_code == 200 else None

def refresh_access_token(refresh_token):
    response = requests.post(
        'https://www.strava.com/oauth/token',
        data={
            'client_id': STRAVA_CLIENT_ID,
            'client_secret': STRAVA_CLIENT_SECRET,
            'refresh_token': refresh_token,
            'grant_type': 'refresh_token'
        }
    )
    return response.json() if response.status_code == 200 else None

def fetch_strava_activities(access_token, after=None, before=None):
    headers = {'Authorization': f'Bearer {access_token}'}
    params = {}
    if after:
        params['after'] = int(after.timestamp())
    if before:
        params['before'] = int(before.timestamp())
    
    response = requests.get('https://www.strava.com/api/v3/athlete/activities', headers=headers, params=params)
    return response.json() if response.status_code == 200 else []
