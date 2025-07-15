from app import app, db
import os

# Path to the instance folder and database file
INSTANCE_FOLDER_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance')
DATABASE_FILE_PATH = os.path.join(INSTANCE_FOLDER_PATH, 'vehicle_parking.db')

def reset_database():
    """Deletes and recreates the database and tables."""
    with app.app_context():
        print("Resetting database...")
        
        # Drop all tables
        db.drop_all()
        print("Existing tables dropped.")
        
        # Create all tables
        db.create_all()
        print("New tables created.")
        
        print("Database has been successfully reset.")

if __name__ == '__main__':
    # Ensure the instance folder exists
    if not os.path.exists(INSTANCE_FOLDER_PATH):
        os.makedirs(INSTANCE_FOLDER_PATH)
        print(f"Created directory: {INSTANCE_FOLDER_PATH}")
        
    reset_database()
