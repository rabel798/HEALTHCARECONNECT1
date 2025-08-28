
# Dr. Richa's Eye Clinic - Web Application

A comprehensive web application for managing an eye clinic, built with Flask and PostgreSQL. This system provides separate interfaces for patients, doctors, assistants, and administrators.

## Features

- **Patient Portal**: Appointment booking, medical records, profile management
- **Doctor Dashboard**: Patient management, prescription creation, appointment viewing
- **Assistant/Optometrist Portal**: Basic eye examinations, prescription management
- **Admin Panel**: Complete clinic management, revenue tracking, staff management
- **Interactive Map**: Location services with directions to the clinic
- **Payment Integration**: Secure payment processing for appointments
- **Email Notifications**: Automated appointment confirmations and reminders

## Tech Stack

- **Backend**: Flask (Python 3.11)
- **Database**: PostgreSQL
- **Frontend**: HTML5, CSS3, JavaScript, Bootstrap 5
- **Maps**: Leaflet.js with OpenStreetMap
- **Authentication**: Flask-Login with Google OAuth integration
- **Forms**: Flask-WTF with CSRF protection

## Prerequisites

- Python 3.11 or higher
- PostgreSQL database
- Google OAuth credentials (for patient login)
- SMTP email configuration

## Installation & Setup

### 1. Environment Variables

Create a `.env` file in the root directory with the following variables:

```env
# Database Configuration
DATABASE_URL=postgresql://username:password@hostname:port/database_name

# Session Security
SESSION_SECRET=your-secure-session-secret-key

# Google OAuth (for patient login)
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret

# Email Configuration
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
MAIL_USE_TLS=True
MAIL_DEFAULT_SENDER=your-email@gmail.com
```

### 2. Install Dependencies

The application will automatically install required packages from `requirements.txt`:

```
flask==3.1.0
flask-wtf==1.2.2
flask-sqlalchemy==3.1.1
flask-login==0.1.3
gunicorn==23.0.0
sqlalchemy==2.0.39
psycopg2-binary==2.9.10
wtforms==3.2.1
email-validator==2.2.0
leaflet==0.0.3
werkzeug==3.1.3
python-dotenv
requests
```

### 3. Database Setup

The application automatically creates database tables and default accounts on first run. Default accounts created:

**Doctor Account:**
- Username: `drricha`
- Password: `admin123`
- Email: `drricha@eyeclinic.com`

**Assistant/Optometrist Account:**
- Username: `assistant`
- Password: `assistant123`
- Email: `assistant@eyeclinic.com`

### 4. Running the Application

#### Development Mode
```bash
python app.py
```

#### Production Mode (using Gunicorn)
```bash
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

The application will be available at:
- Local: `http://localhost:5000`
- Network: `http://0.0.0.0:5000`

## Application Structure

```
├── static/
│   ├── css/           # Stylesheets
│   ├── js/            # JavaScript files
│   ├── img/           # Images and logos
│   └── assets/        # Additional assets
├── templates/
│   ├── admin/         # Admin panel templates
│   ├── doctor/        # Doctor dashboard templates
│   ├── assistant/     # Assistant portal templates
│   ├── patient/       # Patient portal templates
│   ├── auth/          # Authentication templates
│   └── staff/         # Staff verification templates
├── app.py             # Main application file
├── models.py          # Database models
├── forms.py           # WTForms definitions
├── routes.py          # Application routes
└── init_db.py         # Database initialization script
```

## User Roles & Access

### Patients
- Register with email/phone or Google OAuth
- Book appointments online
- View medical records and prescriptions
- Update profile information
- Make payments for consultations

### Doctor (Dr. Richa)
- View all appointments and patient records
- Create detailed prescriptions and treatment plans
- Manage patient medical history
- Review and approve assistant prescriptions

### Assistant/Optometrist
- Conduct basic eye examinations
- Create preliminary prescriptions
- Manage patient check-ins
- View assigned patient records

### Admin
- Complete clinic management
- Revenue and financial tracking
- Staff salary management
- System administration
- Patient and appointment oversight

## Key Features

### Appointment System
- Online booking with calendar integration
- Email confirmations and reminders
- Status tracking (pending, confirmed, completed)
- Payment integration

### Medical Records
- Comprehensive patient history
- Prescription management
- Visual acuity tracking
- Treatment plan documentation

### Location Services
- Interactive clinic location map
- Directions and nearby landmarks
- Public transport information
- Parking details

### Payment Processing
- Secure online payments
- Multiple payment methods
- Transaction history
- Receipt generation

## Security Features

- CSRF protection on all forms
- Session-based authentication
- Password hashing (Werkzeug)
- SQL injection prevention
- Environment variable configuration

## Customization

### Adding New Features
1. Create new routes in `routes.py`
2. Add corresponding templates in `templates/`
3. Update models in `models.py` if needed
4. Add forms in `forms.py`

### Styling
- Main styles in `static/css/style.css`
- Bootstrap 5 for responsive design
- Custom CSS for clinic branding

## Troubleshooting

### Common Issues

1. **Database Connection Error**
   - Verify DATABASE_URL in `.env`
   - Ensure PostgreSQL is running
   - Check database credentials

2. **Google OAuth Not Working**
   - Verify GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET
   - Check OAuth redirect URIs in Google Console

3. **Email Not Sending**
   - Verify SMTP credentials
   - Enable "Less secure app access" or use app passwords

4. **Map Not Loading**
   - Check internet connection
   - Verify Leaflet.js CDN access

### Logs
Application logs are displayed in the console. For production, configure proper logging to files.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes and test thoroughly
4. Submit a pull request

## Support

For technical support or questions about the application:
- Email: drrichaeyeclinic@gmail.com
- Phone: +91 9876543210

## License

This project is proprietary software for Dr. Richa's Eye Clinic.

---

**Note**: This application is designed for Replit deployment. The configuration is optimized for Replit's environment with automatic package installation and database setup.
