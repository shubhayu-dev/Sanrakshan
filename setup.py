#!/usr/bin/env python3
"""
Setup script for Sanrakshan - Student Storage Management System
Helps configure the environment for first-time setup
"""

import os
import secrets
import shutil
from pathlib import Path

def generate_secret_key():
    """Generate a secure Django secret key"""
    return secrets.token_urlsafe(50)

def setup_environment():
    """Set up environment configuration"""
    print("🚀 Setting up Sanrakshan Environment\n")
    
    # Check if .env already exists
    if os.path.exists('.env'):
        response = input("⚠️  .env file already exists. Overwrite? (y/N): ")
        if response.lower() != 'y':
            print("Setup cancelled.")
            return
    
    # Copy .env.example to .env
    if os.path.exists('.env.example'):
        shutil.copy('.env.example', '.env')
        print("✅ Created .env file from template")
    else:
        print("❌ .env.example not found")
        return
    
    # Generate new secret key
    secret_key = generate_secret_key()
    
    # Read .env file
    with open('.env', 'r') as f:
        content = f.read()
    
    # Replace placeholder secret key
    content = content.replace('your-super-secret-key-here-change-this-in-production', secret_key)
    
    # Get college configuration
    print("\n📚 College Configuration:")
    college_name = input("Enter your college name (e.g., IIIT Kottayam): ").strip()
    email_domain = input("Enter email domain (e.g., @iiitkottayam.ac.in): ").strip()
    
    if college_name:
        content = content.replace('Your College Name', college_name)
    if email_domain:
        content = content.replace('@yourcollege.edu', email_domain)
    
    # Database configuration
    print("\n🗄️  Database Configuration:")
    print("1. SQLite (Development - Default)")
    print("2. PostgreSQL (Production)")
    print("3. MySQL (Alternative)")
    
    db_choice = input("Choose database (1-3) [1]: ").strip() or "1"
    
    if db_choice == "2":
        db_name = input("PostgreSQL database name: ").strip()
        db_user = input("PostgreSQL username: ").strip()
        db_pass = input("PostgreSQL password: ").strip()
        db_host = input("PostgreSQL host [localhost]: ").strip() or "localhost"
        db_port = input("PostgreSQL port [5432]: ").strip() or "5432"
        
        db_url = f"postgresql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"
        content = content.replace('sqlite:///db.sqlite3', db_url)
        
    elif db_choice == "3":
        db_name = input("MySQL database name: ").strip()
        db_user = input("MySQL username: ").strip()
        db_pass = input("MySQL password: ").strip()
        db_host = input("MySQL host [localhost]: ").strip() or "localhost"
        db_port = input("MySQL port [3306]: ").strip() or "3306"
        
        db_url = f"mysql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"
        content = content.replace('sqlite:///db.sqlite3', db_url)
    
    # Write updated .env file
    with open('.env', 'w') as f:
        f.write(content)
    
    print("\n✅ Environment configuration completed!")
    print("\n📋 Next steps:")
    print("1. Install dependencies: pip install -r requirements.txt")
    print("2. Run migrations: python manage.py migrate")
    print("3. Create superuser: python manage.py createsuperuser")
    print("4. Start server: python manage.py runserver")
    
    print(f"\n🔑 Your secret key has been generated and saved securely.")
    print("⚠️  Never commit the .env file to version control!")

def main():
    """Main setup function"""
    try:
        setup_environment()
    except KeyboardInterrupt:
        print("\n\nSetup cancelled by user.")
    except Exception as e:
        print(f"\n❌ Error during setup: {e}")

if __name__ == "__main__":
    main()
