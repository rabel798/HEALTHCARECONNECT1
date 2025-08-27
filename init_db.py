
#!/usr/bin/env python3
"""
Database initialization script for PostgreSQL
Run this once to set up your database schema and default accounts
"""

import os
from app import app, db

def main():
    """Initialize the database"""
    print("Starting database initialization...")
    
    with app.app_context():
        try:
            # Drop all tables (fresh start)
            print("Dropping existing tables...")
            db.drop_all()
            
            # Create all tables
            print("Creating new tables...")
            db.create_all()
            
            # Import models
            from models import Doctor, Assistant
            from datetime import date
            
            # Create default doctor account
            print("Creating default doctor account...")
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
            
            # Create default assistant account
            print("Creating default assistant account...")
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
            
            # Commit all changes
            db.session.commit()
            print("✅ Database initialization completed successfully!")
            print("\nDefault Accounts Created:")
            print("Doctor: username='drricha', password='admin123'")
            print("Assistant: username='assistant', password='assistant123'")
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error initializing database: {str(e)}")
            raise

if __name__ == '__main__':
    main()
