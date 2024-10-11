from flask_migrate import init, migrate, upgrade
from app import app, db

def init_db():
    with app.app_context():
        init()
        migrate(message="Initial migration")
        upgrade()

if __name__ == "__main__":
    init_db()
    print("Database migrations initialized and applied successfully.")
