from datetime import datetime
import pandas as pd

def process_activities(activities):
    if not activities:
        return {}

    df = pd.DataFrame(activities)
    df['start_date'] = pd.to_datetime(df['start_date'])
    df['date'] = df['start_date'].dt.date
    df['moving_time'] = pd.to_timedelta(df['moving_time'], unit='s')

    daily_activity = df.groupby('date')['moving_time'].sum().reset_index()
    daily_activity['activity_level'] = daily_activity['moving_time'].dt.total_seconds() / 3600  # Convert to hours

    # Normalize activity levels to a 0-1 scale
    max_activity = daily_activity['activity_level'].max()
    daily_activity['activity_level'] = daily_activity['activity_level'] / max_activity

    return dict(zip(daily_activity['date'].astype(str), daily_activity['activity_level']))
