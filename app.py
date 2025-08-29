import os
import logging
from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from flask_wtf.csrf import CSRFProtect
from flask_login import LoginManager
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Debug: Print environment variables (remove in production)
print(f"GOOGLE_CLIENT_ID loaded: {'Yes' if os.environ.get('GOOGLE_CLIENT_ID') else 'No'}")
print(f"GOOGLE_CLIENT_SECRET loaded: {'Yes' if os.environ.get('GOOGLE_CLIENT_SECRET') else 'No'}")
print(f"SESSION_SECRET loaded: {'Yes' if os.environ.get('SESSION_SECRET') else 'No'}")

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Create base class for SQLAlchemy models
class Base(DeclarativeBase):
    pass

# Initialize extensions
db = SQLAlchemy(model_class=Base)
csrf = CSRFProtect()
login_manager = LoginManager()

# Create the Flask application
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")

# Configure session settings for better persistence
app.config['SESSION_COOKIE_SECURE'] = False  # Set to True in production with HTTPS
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['PERMANENT_SESSION_LIFETIME'] = 3600  # 1 hour

# Email configuration
app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 587))
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME', 'drrichaeyeclinic@gmail.com')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD', 'onlg iqtn eizf vehv')
app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', 'True').lower() == 'true'
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER', 'drrichaeyeclinic@gmail.com')

# Google OAuth configuration
app.config['GOOGLE_CLIENT_ID'] = os.environ.get('GOOGLE_CLIENT_ID')
app.config['GOOGLE_CLIENT_SECRET'] = os.environ.get('GOOGLE_CLIENT_SECRET')  


# Configure the database - PostgreSQL
database_url = os.environ.get('DATABASE_URL')
if database_url and database_url.startswith('postgres://'):
    # Fix for newer SQLAlchemy versions
    database_url = database_url.replace('postgres://', 'postgresql://', 1)

app.config["SQLALCHEMY_DATABASE_URI"] = database_url or "postgresql://localhost/drricha_dev"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize extensions with app
db.init_app(app)
csrf.init_app(app)
login_manager.init_app(app)
login_manager.login_view = 'patient_login'

# User loader function for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    from models import Doctor, Assistant, Admin, Patient
    try:
        if user_id.startswith('doctor_'):
            return Doctor.query.get(int(user_id.split('_')[1]))
        elif user_id.startswith('assistant_'):
            return Assistant.query.get(int(user_id.split('_')[1]))
        elif user_id.startswith('admin_'):
            return Admin.query.get(int(user_id.split('_')[1]))
        else:
            return Patient.query.get(int(user_id))
    except (ValueError, AttributeError):
        return None

# Import routes after app is created
from routes import *

# Initialize database function
def init_database():
    """Initialize database tables and default accounts"""
    try:
        # Import here to avoid circular imports
        from models import Doctor, Assistant
        from datetime import date
        
        # Create all tables first
        db.create_all()
        print('Database tables initialized')

        # Check if we need to create default accounts
        try:
            # Create default doctor account if it doesn't exist
            doctor = Doctor.query.filter_by(username='drricha').first()
            if not doctor:
                doctor = Doctor(
                    username='drricha',
                    email='drricha@eyeclinic.com',
                    full_name='Dr. Richa Sharma',
                    mobile_number='9876543210',
                    qualifications='MBBS, MS, FPOS',
                    specialization='Ophthalmology, Pediatric Eye Care'
                )
                doctor.set_password('admin123')
                db.session.add(doctor)
                print('Default doctor account created')

            # Create optometrist account if it doesn't exist
            assistant = Assistant.query.filter_by(username='assistant').first()
            if not assistant:
                assistant = Assistant(
                    username='assistant',
                    email='assistant@eyeclinic.com',
                    full_name='Clinic Optometrist',
                    mobile_number='9876543211',
                    position='Optometrist',
                    joining_date=date.today()
                )
                assistant.set_password('assistant123')
                db.session.add(assistant)
                print('Default optometrist account created')

            # Commit changes
            db.session.commit()
            print('Database initialization completed successfully')
            
        except Exception as query_error:
            # If there's an issue with queries, just create tables and continue
            print(f'Note: {str(query_error)}')
            print('Tables created successfully. You may need to run init_db.py separately.')
        
    except Exception as e:
        db.session.rollback()
        print(f'Error initializing database: {str(e)}')
        # Don't raise the error, just print it and continue
        print('Continuing without default accounts...')

# Initialize database when app starts
with app.app_context():
    init_database()

# Start the reminder service
try:
    from reminder_system import start_reminder_service
    start_reminder_service()
    print("Appointment reminder service initialized")
except Exception as e:
    print(f"Could not start reminder service: {str(e)}")

# Register error handlers
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)