"""
Script to create default admin and guest accounts
"""
import os
import sys
from app import app, db  
from models import User

# Create a default admin and guest account if they don't exist
def create_default_users():
    with app.app_context():
        # Check if admin user exists
        admin_user = User.query.filter_by(username='admin').first()
        if not admin_user:
            print("Creating admin user...")
            admin = User(
                username='admin',
                email='admin@smartfilevault.app',
                is_admin=True,
                is_guest=False
            )
            admin.set_password('admin123')
            db.session.add(admin)
            
        # Check if guest user exists
        guest_user = User.query.filter_by(username='guest').first()
        if not guest_user:
            print("Creating guest user...")
            guest = User(
                username='guest',
                email='guest@smartfilevault.app',
                is_admin=False,
                is_guest=True
            )
            guest.set_password('guest123')
            db.session.add(guest)
            
        # Commit changes
        db.session.commit()
        print("Default users created successfully!")

if __name__ == '__main__':
    create_default_users()