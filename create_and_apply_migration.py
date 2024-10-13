from flask_migrate import Migrate
from app import app, db
from models import User

migrate = Migrate(app, db)

if __name__ == '__main__':
    with app.app_context():
        migrate.init_app(app, db)
        migrate.migrate()
        migrate.upgrade()

    print("Migration completed successfully.")
