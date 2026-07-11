try:
    from app import app, seed_database
except ImportError:
    from trekking_management_app.app import app, seed_database


with app.app_context():
    seed_database()
    print("Database initialized successfully.")
