from app import app, db
from models import User

def create_test_user():
    with app.app_context():
        if not User.query.filter_by(username='testuser').first():
            test_user = User(username='testuser', email='testuser@example.com')
            test_user.set_password('testpassword')
            db.session.add(test_user)
            db.session.commit()
            print("Test user created successfully.")
        else:
            print("Test user already exists.")

if __name__ == "__main__":
    create_test_user()
