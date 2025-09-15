# 🎓 Sanrakshan - Student Storage Management System

Sanrakshan is a Django-based web application designed for educational institutions to manage student belongings storage efficiently. Students can register their items for temporary storage and receive QR codes for easy retrieval, while staff can scan codes to process claims seamlessly.

Perfect for hostels, libraries, and campus facilities managing student belongings during breaks, events, or relocations.

## ✨ Key Features

- **Student Registration & Authentication** with college email validation
- **Item Storage Management** with detailed tracking
- **QR Code Generation** for secure item retrieval
- **Staff Interface** for processing claims seamlessly
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
- **Student Interface**: http://127.0.0.1:8000/
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

### College Customization
1. **Email Domain**: Update `COLLEGE_EMAIL_DOMAIN` in `.env`
2. **Roll Number Format**: Modify regex in `accounts/models.py`
3. **Departments**: Update choices in `accounts/models.py`

## 📱 Usage

### For Students
1. **Register** with college email and roll number
2. **Login** with username/email and password
3. **Create Storage Entry** with item details
4. **Generate QR Code** for item retrieval
5. **View History** of all storage activities

### For Staff
1. **Login** with staff credentials
2. **Scan QR Codes** to view student items
3. **Process Claims** when students collect items
4. **Manage Storage** through admin interface

## 🗄️ Database Schema

### Core Models
- **User**: Authentication and basic info
- **StudentProfile**: College-specific student data
- **StorageEntry**: Individual storage sessions
- **StoredItem**: Items within each storage entry
- **QRCodeImage**: Generated QR codes for entries
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
