from flask_migrate import Migrate, upgrade
from app import app, db
from models import User, Activity

migrate = Migrate(app, db)

if __name__ == '__main__':
    with app.app_context():
        migrate.init_app(app, db)
        upgrade()

    print("Migration completed successfully.")
