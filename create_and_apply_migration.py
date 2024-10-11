from app import app, db
from flask_migrate import upgrade, migrate, init, stamp
from flask.cli import with_appcontext

@with_appcontext
def create_migration():
    migrate(message="Add Strava fields to User and Workout models")

@with_appcontext
def apply_migration():
    upgrade()

if __name__ == "__main__":
    with app.app_context():
        init()  # Initialize migrations if not already done
        create_migration()
        apply_migration()
    print("Migration created and applied successfully.")
