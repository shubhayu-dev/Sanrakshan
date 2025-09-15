#!/usr/bin/env python
"""
Create a superuser for testing the admin interface.
"""
import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'student_storage_system.settings')
django.setup()

from django.contrib.auth import get_user_model
from accounts.models import StudentProfile

User = get_user_model()

def create_superuser():
    # Create superuser if it doesn't exist
    if not User.objects.filter(username='admin').exists():
        admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@storage.system',
            password='admin123',
            first_name='System',
            last_name='Administrator'
        )
        print(f"Created superuser: {admin_user.username}")
        
        # Create a student profile for the admin (optional)
        if not hasattr(admin_user, 'student_profile'):
            try:
                profile = StudentProfile.objects.create(
                    user=admin_user,
                    roll_number='ADMIN001',
                    department='OTHER',
                    year=1,
                    phone_number='+91 9999999999',
                    hostel_room='Admin Office',
                    emergency_contact='+91 9999999999'
                )
                print(f"Created admin profile: {profile}")
            except Exception as e:
                print(f"Admin profile creation failed (this is okay): {e}")
    else:
        print("Superuser 'admin' already exists")

    # Create some test users
    test_users = [
        {
            'username': 'student1',
            'email': 'student1@college.edu',
            'password': 'test123',
            'first_name': 'John',
            'last_name': 'Doe',
            'roll_number': '20CS001',
            'department': 'CSE',
            'year': 2
        },
        {
            'username': 'student2',
            'email': 'student2@college.edu',
            'password': 'test123',
            'first_name': 'Jane',
            'last_name': 'Smith',
            'roll_number': '20EC015',
            'department': 'ECE',
            'year': 3
        }
    ]
    
    for user_data in test_users:
        if not User.objects.filter(username=user_data['username']).exists():
            user = User.objects.create_user(
                username=user_data['username'],
                email=user_data['email'],
                password=user_data['password'],
                first_name=user_data['first_name'],
                last_name=user_data['last_name']
            )
            
            # Check if profile already exists (from signal)
            try:
                profile = StudentProfile.objects.get(user=user)
                # Update the existing profile
                profile.roll_number = user_data['roll_number']
                profile.department = user_data['department']
                profile.year = user_data['year']
                profile.phone_number = f'+91987654320{user_data["year"]}'
                profile.hostel_room = f'{user_data["department"]}-{user_data["year"]}01'
                profile.emergency_contact = '+919876543210'
                profile.save()
                print(f"Updated test user profile: {user.username} ({profile.roll_number})")
            except StudentProfile.DoesNotExist:
                profile = StudentProfile.objects.create(
                    user=user,
                    roll_number=user_data['roll_number'],
                    department=user_data['department'],
                    year=user_data['year'],
                    phone_number=f'+91987654320{user_data["year"]}',
                    hostel_room=f'{user_data["department"]}-{user_data["year"]}01',
                    emergency_contact='+919876543210'
                )
                print(f"Created test user: {user.username} ({profile.roll_number})")
        else:
            print(f"Test user '{user_data['username']}' already exists")

if __name__ == "__main__":
    create_superuser()
    print("\n=== Login Credentials ===")
    print("Admin: admin / admin123")
    print("Student 1: student1 / test123")  
    print("Student 2: student2 / test123")
    print("=========================")
