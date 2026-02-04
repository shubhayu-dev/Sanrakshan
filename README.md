# 🎓 Sanrakshan - Student Storage Management System

Sanrakshan is a Django-based web application designed for educational institutions to manage student belongings storage efficiently. Students can register their items for temporary storage and receive QR codes for easy retrieval, while staff can scan codes to process claims seamlessly.

Perfect for hostels, libraries, and campus facilities managing student belongings during breaks, events, or relocations.

## ✨ Key Features

- **Unique Code System** for secure, specialized item retrieval (Validation Codes)
- **Staff Dashboard** for processing claims and verification
- **Secure Verification** via admin interface
- **Student Registration & Authentication** with college email validation
- **Item Storage Management** with detailed tracking
- **Password Reset** via email verification
- **Responsive Design** with Bootstrap 5
- **Privacy-Focused** with proper data protection

## 🎯 Use Cases

- **Hostel Storage** during semester breaks
- **Library Item Management** for temporary holds
- **Event Storage** for student belongings during functions
- **Campus Relocations** and room changes
- **Emergency Storage** during maintenance

## 🚀 Quick Start

### 1. Clone & Setup
```bash
git clone <repository-url>
cd sanrakshan
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Environment Configuration
```bash
cp .env.example .env
# Edit .env with your settings (see Configuration section)
```

### 3. Database Setup
```bash
python manage.py migrate
python manage.py createsuperuser
```

### 4. Run Development Server
```bash
python manage.py runserver
```

### 5. Access the System
### 5. Access the System
- **Student Interface**: http://127.0.0.1:8000/storage/dashboard/
- **Staff Dashboard**: http://127.0.0.1:8000/storage/staff/dashboard/
- **Admin Interface**: http://127.0.0.1:8000/admin/

## ⚙️ Configuration

### Environment Variables (.env)
```env
# Security
SECRET_KEY=your-secret-key-here
DEBUG=True

# Database
DATABASE_URL=sqlite:///db.sqlite3

# Email (for password reset)
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend

# College Settings
COLLEGE_EMAIL_DOMAIN=@yourcollege.edu
TIME_ZONE=Asia/Kolkata
```
### Visual Guide


**Initial Screen to Login**

<img width="1905" height="972" alt="Screenshot from 2026-01-21 20-49-15" src="https://github.com/user-attachments/assets/82421a97-5c3d-4134-a1c9-c6a7483e23a6" />


**Main Dashboard**
- Store Items : Store the items 
- Claim Items : Claim the items

<img width="1905" height="972" alt="Screenshot from 2026-01-21 20-52-58" src="https://github.com/user-attachments/assets/55062197-fe01-4a47-9371-4e5d903b3a48" />


**Store Items**
- Enter all the item details that are to be kept
  
<img width="1905" height="972" alt="Screenshot from 2026-01-21 20-55-15" src="https://github.com/user-attachments/assets/bdfea773-a010-428b-a022-60dede10ed8c" />


**Staff Dashboard**
- Central hub for verification and claims
- Live statistics and recent activity feed
- Manual code verification input

*(Screenshot placeholder for Staff Dashboard)*

**Unique Code Display**
- Shows secure 8-character code
- Status indicators (Active/Claimed/Inactive)
- Printer-friendly format

<img width="1905" height="972" alt="Screenshot from 2026-01-21 20-54-48" src="https://github.com/user-attachments/assets/b7b26573-eb39-41e4-9e4c-5173ffd304db" />

**Dashboard after claiming items**

<img width="1905" height="972" alt="Screenshot from 2026-01-21 20-55-06" src="https://github.com/user-attachments/assets/f0f81b54-3ae9-4510-bc6f-9a12c8dc9a81" />


**Profile**

<img width="950" height="967" alt="image" src="https://github.com/user-attachments/assets/f579d361-1e3f-4fac-b310-fc040b072bf7" />


### College Customization
1. **Email Domain**: Update `COLLEGE_EMAIL_DOMAIN` in `.env`
2. **Roll Number Format**: Modify regex in `accounts/models.py`
3. **Departments**: Update choices in `accounts/models.py`

## 📱 Usage

### For Students
1. **Register** with college email and roll number
2. **Login** with username/email and password
3. **Create Storage Entry** with item details
4. **Get Unique Code**: A secure 8-character code (e.g., `A7B2-9XY1`) is generated.
5. **View History** of all storage activities

### For Staff
1. **Login** with staff credentials (or admin)
2. **Access Staff Dashboard**: `/storage/staff/dashboard/`
3. **Verify Codes**: Enter student's unique code to view items and owner details.
4. **Process Claims**: Mark items as returned with a single click.
5. **Manage Storage** through admin interface as needed.

## 🗄️ Database Schema

### Core Models
- **User**: Authentication and basic info
- **StudentProfile**: College-specific student data
- **StorageEntry**: Individual storage sessions
- **StoredItem**: Items within each storage entry
- **UniqueCode**: Generated unique validation codes
- **PasswordResetCode**: Email-based password reset

## 🔒 Security Features

- **Email Domain Validation** for student registration
- **Password Hashing** with Django's PBKDF2
- **CSRF Protection** on all forms
- **Permission-Based Access** (student vs staff views)
- **Environment Variables** for sensitive configuration
- **Privacy Protection** via .gitignore exclusions

## 🛠️ Production Deployment

### Database Configuration
```env
# PostgreSQL (Recommended)
DATABASE_URL=postgresql://user:pass@localhost:5432/storage_db

# MySQL (Alternative)
DATABASE_URL=mysql://user:pass@localhost:3306/storage_db
```

### Email Configuration
```env
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
```

### Security Settings
```env
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
SECURE_SSL_REDIRECT=True
```

## 📁 Project Structure

```
sanrakshan/
├── accounts/              # User management
├── storage/              # Storage functionality  
├── qr_codes/            # QR code system
├── templates/           # HTML templates
├── static/             # CSS, JS, images
├── requirements.txt    # Python dependencies
├── .env.example       # Environment template
└── README.md         # This file
```

## 🔧 Development

### Running Tests
```bash
python manage.py test
```

### Creating Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### Collecting Static Files
```bash
python manage.py collectstatic
```

## 📋 Requirements

- Python 3.8+
- Django 4.2+
- SQLite (development) / PostgreSQL (production)
- Modern web browser with JavaScript enabled

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 🆘 Support

For issues and questions:
1. Check the documentation
2. Review existing issues
3. Create a new issue with detailed information

---

**Sanrakshan - Smart Storage Management for Educational Institutions**

## 🚨 Troubleshooting Guide

### Common Issues and Solutions

#### 1. Server Won't Start / Hangs
**Problem**: Django server hangs during startup
**Solution**:
```bash
# Create required directories
mkdir -p logs static

# Run with specific flags to avoid hanging
python manage.py runserver --noreload --nothreading
```

#### 2. Database Errors (OperationalError)
**Problem**: "no such table" or "OperationalError" when accessing pages
**Solution**:
```bash
# Run migrations to create database tables
python manage.py migrate

# If issues persist, reset database
rm db.sqlite3
python manage.py migrate
python manage.py createsuperuser
```

#### 3. Missing StudentProfile Error
**Problem**: "No StudentProfile matches the given query"
**Solution**:
```bash
# Create student profiles for existing users
python manage.py shell -c "
from accounts.models import User, StudentProfile
for user in User.objects.all():
    if not hasattr(user, 'student_profile'):
        StudentProfile.objects.create(
            user=user,
            roll_number=f'2024BCS{user.id:04d}',
            department='BCS',
            year=2,
            phone_number='9876543210'
        )
        print(f'Created profile for {user.username}')
"
```

#### 4. Module Import Errors
**Problem**: "ModuleNotFoundError" for packages like `dj_database_url`
**Solution**:
```bash
# Ensure virtual environment is activated
source venv/bin/activate

# Install all requirements
pip install -r requirements.txt

# If specific package missing
pip install dj-database-url python-decouple
```

#### 5. Permission Denied Errors
**Problem**: Cannot access certain pages or features
**Solution**:
```bash
# Create superuser account
python manage.py createsuperuser

# Or create via shell with profile
python manage.py shell -c "
from accounts.models import User, StudentProfile
user = User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
StudentProfile.objects.create(
    user=user,
    roll_number='2024BCS0001',
    department='BCS',
    year=1,
    phone_number='9876543210'
)
"
```

### 6. Static Files Not Loading
**Problem**: CSS/JS files not loading properly
**Solution**:
```bash
# Create static directory
mkdir -p static

# Collect static files (for production)
python manage.py collectstatic

# For development, ensure DEBUG=True in .env
```

## 🔧 Advanced Setup

### Complete First-Time Setup Script
```bash
#!/bin/bash
# Complete setup script for Sanrakshan

# 1. Create virtual environment
python -m venv venv
source venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Create required directories
mkdir -p logs static media

# 4. Setup environment
cp .env.example .env
echo "Please edit .env file with your settings"

# 5. Database setup
python manage.py migrate

# 6. Create superuser
python manage.py shell -c "
from accounts.models import User, StudentProfile
if not User.objects.filter(username='admin').exists():
    user = User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    StudentProfile.objects.create(
        user=user,
        roll_number='2024BCS0001',
        department='BCS',
        year=1,
        phone_number='9876543210'
    )
    print('Superuser created: admin/admin123')
"

# 7. Start server
python manage.py runserver
```

### Environment Variables Explained

| Variable | Description | Example |
|----------|-------------|---------|
| `SECRET_KEY` | Django secret key for security | `django-insecure-xyz...` |
| `DEBUG` | Enable debug mode (True/False) | `True` |
| `ALLOWED_HOSTS` | Comma-separated allowed hosts | `localhost,127.0.0.1` |
| `DATABASE_URL` | Database connection string | `sqlite:///db.sqlite3` |
| `EMAIL_HOST` | SMTP server for emails | `smtp.gmail.com` |
| `EMAIL_HOST_USER` | Email username | `your-email@gmail.com` |
| `EMAIL_HOST_PASSWORD` | Email password/app password | `your-app-password` |

### Production Checklist

- [ ] Set `DEBUG=False` in production
- [ ] Configure proper `ALLOWED_HOSTS`
- [ ] Use PostgreSQL/MySQL instead of SQLite
- [ ] Set up proper email backend (SMTP)
- [ ] Configure static file serving (nginx/Apache)
- [ ] Set up SSL certificates
- [ ] Configure backup strategy
- [ ] Set up monitoring and logging
- [ ] Use environment variables for all secrets
- [ ] Enable security middleware

### Testing the Installation

```bash
# Test basic functionality
python manage.py check

# Test database connection
python manage.py shell -c "from django.db import connection; connection.ensure_connection(); print('DB OK')"

# Test user creation
python manage.py shell -c "from accounts.models import User; print('Users:', User.objects.count())"

# Test server startup
timeout 5s python manage.py runserver --noreload || echo "Server test complete"
```

## 📊 System Requirements

### Minimum Requirements
- **OS**: Linux, macOS, or Windows
- **Python**: 3.8 or higher
- **RAM**: 512MB minimum, 1GB recommended
- **Storage**: 100MB for application, additional for database
- **Browser**: Modern browser with JavaScript enabled

### Recommended Production Setup
- **OS**: Ubuntu 20.04+ or CentOS 8+
- **Python**: 3.9+
- **RAM**: 2GB+
- **Storage**: 10GB+ with SSD
- **Database**: PostgreSQL 12+
- **Web Server**: nginx + gunicorn
- **SSL**: Let's Encrypt certificates

## 🔍 Monitoring and Maintenance

### Log Files
- **Django Logs**: `logs/django.log`
- **Error Logs**: Check Django admin for error reports
- **Access Logs**: Web server logs (nginx/Apache)

### Regular Maintenance
```bash
# Database cleanup (monthly)
python manage.py shell -c "
from storage.models import StorageEntry
from django.utils import timezone
from datetime import timedelta

# Clean up old expired entries (older than 6 months)
cutoff = timezone.now() - timedelta(days=180)
old_entries = StorageEntry.objects.filter(
    status='expired',
    updated_at__lt=cutoff
)
print(f'Cleaning up {old_entries.count()} old entries')
old_entries.delete()
"

# Update dependencies (quarterly)
pip list --outdated
pip install -r requirements.txt --upgrade

# Database backup (weekly)
python manage.py dumpdata > backup_$(date +%Y%m%d).json
```

---

**Need Help?** 
- Check the troubleshooting section above
- Review Django documentation: https://docs.djangoproject.com/
- Create an issue with detailed error messages and system information
