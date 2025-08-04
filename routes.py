import os
import random
import string
from datetime import datetime, timedelta
from flask import render_template, request, redirect, url_for, flash, jsonify, session
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from sqlalchemy import desc
from flask_login import login_user, logout_user, current_user, login_required
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, Email
from app import app, db
from models import Patient, Appointment, MedicalRecord, Payment, Review, Admin, OTP, Doctor, Assistant, Salary, Treatment, DoctorPrescription, OptometristPrescription
from forms import (
    AppointmentForm, PaymentForm, ReviewForm, DoctorLoginForm, AssistantLoginForm, AdminLoginForm, PatientLoginForm, PatientRegistrationForm, OTPVerificationForm, PrescriptionForm, DoctorPrescriptionForm, OptometristPrescriptionForm, SalaryForm
)
import requests

# Add context processor to make current datetime available to all templates
@app.context_processor
def inject_now():
    return {'now': datetime.now()}

@app.route('/')
def index():
    """Home page route"""


    # Fetch 3 most recent approved reviews
    recent_reviews = Review.query.filter_by(is_approved=True).order_by(desc(Review.created_at)).limit(3).all()
    return render_template('index.html', reviews=recent_reviews)

@app.route('/services')
def services():
    """Services page route"""
    return render_template('services.html')

@app.route('/location')
def location():
    """Location page route"""
    return render_template('location.html')

@app.route('/reviews', methods=['GET', 'POST'])
def reviews():
    """Reviews page route with submission form"""
    form = ReviewForm()

    if form.validate_on_submit():
        # Create new review (unapproved by default)
        new_review = Review(
            patient_name=form.patient_name.data,
            rating=int(form.rating.data),
            review_text=form.review_text.data,
            is_approved=False  # Requires admin approval
        )
        db.session.add(new_review)
        try:
            db.session.commit()
            flash('Thank you for your review! It will be displayed after approval.', 'success')
            return redirect(url_for('reviews'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error submitting review: {str(e)}', 'danger')

    # Get all approved reviews
    approved_reviews = Review.query.filter_by(is_approved=True).order_by(desc(Review.created_at)).all()
    return render_template('reviews.html', reviews=approved_reviews, form=form)

@app.route('/appointment', methods=['GET', 'POST'])
def appointment():
    """Appointment booking page route"""
    form = AppointmentForm()

    # If the user is logged in, pre-fill the form
    if current_user.is_authenticated and isinstance(current_user, Patient):
        if request.method == 'GET':
            form.full_name.data = current_user.full_name
            form.mobile_number.data = current_user.mobile_number
            form.email.data = current_user.email
            form.age.data = current_user.age

    if form.validate_on_submit():
        if current_user.is_authenticated and isinstance(current_user, Patient):
            # Use the logged in patient
            patient = current_user
        else:
            # Check if patient exists by mobile number
            patient = Patient.query.filter_by(mobile_number=form.mobile_number.data).first()

            # If patient doesn't exist, create new patient
            if not patient:
                patient = Patient(
                    full_name=form.full_name.data,
                    mobile_number=form.mobile_number.data,
                    email=form.email.data,
                    age=form.age.data,
                    sex=form.sex.data
                )
                db.session.add(patient)
                db.session.flush()  # To get the patient ID before commit

        # Create new appointment
        new_appointment = Appointment(
            patient_id=patient.id,
            appointment_date=form.appointment_date.data,
            appointment_time=form.appointment_time.data,
            primary_issue=form.primary_issue.data,
            referral_info=form.referral_info.data,
            status='scheduled'
        )
        db.session.add(new_appointment)

        try:
            db.session.commit()
            # Store appointment ID in session for payment process
            session['appointment_id'] = new_appointment.id

            # Send confirmation email
            subject = "Appointment Confirmation - Dr. Richa's Eye Clinic"
            message = f"""
            Dear {patient.full_name},

            Your appointment has been confirmed for {new_appointment.appointment_date.strftime('%d %B, %Y')} at {new_appointment.appointment_time.strftime('%I:%M %p')}.

            Primary Issue: {new_appointment.primary_issue}
            Appointment ID: #{new_appointment.id}

            Location: First floor, DVR Town Centre, near to IGUS private limited, 
            Mandur, Budigere Road (New Airport Road), Bengaluru, Karnataka 560049

            Best regards,
            Dr. Richa's Eye Clinic
            """
            send_email_notification(patient.email, subject, message)

            return redirect(url_for('payment'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error booking appointment: {str(e)}', 'danger')
            return redirect(url_for('appointment'))

    # Pass default date (tomorrow) and available time slots to the template
    tomorrow = datetime.now() + timedelta(days=1)
    default_date = tomorrow.strftime('%Y-%m-%d')

    return render_template('appointment.html', form=form, default_date=default_date)



@app.route('/payment', methods=['GET', 'POST'])
def payment():
    """Payment processing page route"""
    appointment_id = session.get('appointment_id')
    if not appointment_id:
        flash('No active appointment found', 'warning')
        return redirect(url_for('appointment'))

    try:
        appointment = Appointment.query.get_or_404(appointment_id)
        consultation_fee = 500.00

        # Create payment record - cash payment at clinic
        new_payment = Payment(
            appointment_id=appointment_id,
            amount=consultation_fee,
            payment_method='cash',
            status='pending'
        )
        db.session.add(new_payment)

        # Update appointment payment status
        appointment.payment_status = 'pending'
        db.session.commit()

        flash('Appointment booked successfully! Please pay ₹500 at the clinic.', 'success')
        return redirect(url_for('success'))
    except Exception as e:
        db.session.rollback()
        flash(f'Error processing appointment: {str(e)}', 'danger')
        return redirect(url_for('appointment'))



@app.route('/success')
def success():
    """Success page after completing appointment and payment"""
    return render_template('success.html')

# API route for checking available time slots
@app.route('/api/available-slots', methods=['GET'])
def available_slots():
    selected_date = request.args.get('date')

    # If no date provided, return empty list
    if not selected_date:
        return jsonify([])

    try:
        # Convert selected_date string to date object
        selected_date = datetime.strptime(selected_date, '%Y-%m-%d').date()

        # Check if the selected date is Sunday (weekday 6)
        is_sunday = selected_date.weekday() == 6

        # Define available slots based on day of week
        if is_sunday:
            # Sunday slots (10 AM to 1 PM with 30-minute intervals)
            all_slots = [
                "10:00", "10:30", "11:00", "11:30", "12:00", "12:30", "13:00"
            ]
        else:
            # Monday to Saturday slots (5 PM to 8 PM with 30-minute intervals)
            all_slots = [
                "17:00", "17:30", "18:00", "18:30", "19:00", "19:30", "20:00"
            ]

        # Get all appointments for the selected date
        booked_appointments = Appointment.query.filter_by(appointment_date=selected_date).all()

        # Get the booked time slots
        booked_slots = [appt.appointment_time.strftime('%H:%M') for appt in booked_appointments]

        # Filter out booked slots
        available_slots = [slot for slot in all_slots if slot not in booked_slots]

        return jsonify(available_slots)
    except Exception as e:
        return jsonify({"error": str(e)}), 400


# Patient Authentication Routes
@app.route('/patient/register', methods=['GET', 'POST'])
def patient_register():
    """Patient registration route"""
    # If already logged in, redirect to patient dashboard
    if current_user.is_authenticated:
        return redirect(url_for('patient_dashboard'))

    form = PatientRegistrationForm()
    if form.validate_on_submit():
        try:
            # Check if email or mobile already exists
            existing_patient = Patient.query.filter(
                (Patient.email == form.email.data) | 
                (Patient.mobile_number == form.mobile_number.data)
            ).first()

            if existing_patient:
                flash('A patient with this email or mobile number already exists.', 'danger')
                return redirect(url_for('patient_register'))

            # Generate 6-digit OTP
            otp_code = ''.join(random.choices(string.digits, k=6))

            # Set expiry time (30 minutes)
            expires_at = datetime.utcnow() + timedelta(minutes=30)

            # Store OTP in database
            new_otp = OTP(
                email=form.email.data,
                otp_code=otp_code,
                expires_at=expires_at
            )
            db.session.add(new_otp)
            db.session.commit()

            # Store registration data in session for later use
            session['registration_data'] = {
                'full_name': form.full_name.data,
                'mobile_number': form.mobile_number.data,
                'email': form.email.data,
                'age': form.age.data,
                'sex': form.sex.data,
                'password': form.password.data
            }

            # Send OTP via email
            subject = "Your OTP for Dr. Richa's Eye Clinic Registration"
            message = f"""
            Dear {form.full_name.data},

            Your OTP for registration is: {otp_code}

            This OTP will expire in 30 minutes.

            Best regards,
            Dr. Richa's Eye Clinic
            """
            try:
                send_email_notification(form.email.data, subject, message)
                flash('OTP has been sent to your email address', 'success')
            except Exception as email_error:
                print(f"Email error: {str(email_error)}")
                flash('OTP has been generated. Please proceed to verification.', 'info')

            # Redirect to OTP verification page
            return redirect(url_for('verify_otp', email=form.email.data))

        except Exception as e:
            db.session.rollback()
            print(f"Registration error: {str(e)}")
            flash('An error occurred during registration. Please try again.', 'danger')
            return redirect(url_for('patient_register'))

    return render_template('patient/register.html', form=form)


@app.route('/patient/verify-otp/<email>', methods=['GET', 'POST'])
def verify_otp(email):
    """OTP verification route"""
    # If already logged in, redirect to patient dashboard
    if current_user.is_authenticated:
        return redirect(url_for('patient_dashboard'))

    # Check if we have registration data
    if 'registration_data' not in session:
        flash('Registration session expired. Please register again.', 'warning')
        return redirect(url_for('patient_register'))

    form = OTPVerificationForm()
    form.email.data = email

    if form.validate_on_submit():
        # Find the most recent OTP for this email
        otp_record = OTP.query.filter_by(
            email=email,
            is_verified=False
        ).order_by(desc(OTP.created_at)).first()

        if not otp_record:
            flash('OTP record not found or already verified. Please request a new OTP.', 'danger')
            return redirect(url_for('patient_register'))

        if otp_record.is_expired():
            flash('OTP has expired. Please request a new OTP.', 'danger')
            return redirect(url_for('patient_register'))

        if otp_record.otp_code != form.otp.data:
            flash('Invalid OTP. Please try again.', 'danger')
            return redirect(url_for('verify_otp', email=email))

        # OTP verified, create patient account
        registration_data = session['registration_data']
        new_patient = Patient(
            full_name=registration_data['full_name'],
            mobile_number=registration_data['mobile_number'],
            email=registration_data['email'],
            age=registration_data['age'],
            sex=registration_data['sex'],
            is_registered=True
        )
        new_patient.set_password(registration_data['password'])

        # Mark OTP as verified
        otp_record.is_verified = True

        db.session.add(new_patient)

        try:
            db.session.commit()

            # Clear session data
            session.pop('registration_data', None)

            # Log in the user
            login_user(new_patient)

            flash('Registration successful!', 'success')
            return redirect(url_for('patient_dashboard'))

        except Exception as e:
            db.session.rollback()
            flash(f'Error creating account: {str(e)}', 'danger')

    return render_template('patient/verify_otp.html', form=form, email=email)


@app.route('/patient/gmail-login', methods=['GET', 'POST'])
def patient_gmail_login():
    """Patient Gmail OTP login route"""
    # If already logged in, redirect to patient dashboard
    if current_user.is_authenticated:
        return redirect(url_for('patient_dashboard'))

    # Create a simple form to collect email for OTP
    class GmailLoginForm(FlaskForm):
        email = StringField('Email Address', validators=[DataRequired(), Email()])
        submit = SubmitField('Send OTP')

    form = GmailLoginForm()

    if form.validate_on_submit():
        email = form.email.data

        # Check if patient exists with this email
        patient = Patient.query.filter_by(email=email).first()

        if not patient:
            # Create a non-registered patient record with email only
            patient = Patient(
                full_name="Gmail User",  # Will be updated after login
                mobile_number="0000000000",  # Will be updated after login
                email=email,
                age=1,  # Will be updated after login
                is_registered=False
            )
            db.session.add(patient)
            db.session.flush()

        # Generate 6-digit OTP
        otp_code = ''.join(random.choices(string.digits, k=6))

        # Set expiry time (30 minutes)
        expires_at = datetime.utcnow() + timedelta(minutes=30)

        # Store OTP in database
        new_otp = OTP(
            email=email,
            otp_code=otp_code,
            expires_at=expires_at
        )
        db.session.add(new_otp)

        try:
            db.session.commit()

            # Send OTP via email
            subject = "Your OTP for Dr. Richa's Eye Clinic Login"
            message = f"""
            Dear {patient.full_name if patient else "User"},

            Your OTP for login is: {otp_code}

            This OTP will expire in 30 minutes.

            Best regards,
            Dr. Richa's Eye Clinic
            """
            if send_email_notification(email, subject, message):
                flash('OTP has been sent to your email address', 'success')
            else:
                flash('Error sending OTP. Please try again.', 'danger')

            # Redirect to OTP verification page
            return redirect(url_for('verify_login_otp', email=email))

        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'danger')

    return render_template('patient/gmail_login.html', form=form)


@app.route('/patient/verify-login-otp/<email>', methods=['GET', 'POST'])
def verify_login_otp(email):
    """Verify OTP for Gmail login"""
    # If already logged in, redirect to patient dashboard
    if current_user.is_authenticated:
        return redirect(url_for('patient_dashboard'))

    form = OTPVerificationForm()
    form.email.data = email

    if form.validate_on_submit():
        # Find the most recent OTP for this email
        otp_record = OTP.query.filter_by(
            email=email,
            is_verified=False
        ).order_by(desc(OTP.created_at)).first()

        if not otp_record:
            flash('OTP record not found or already verified. Please request a new OTP.', 'danger')
            return redirect(url_for('patient_gmail_login'))

        if otp_record.is_expired():
            flash('OTP has expired. Please request a new OTP.', 'danger')
            return redirect(url_for('patient_gmail_login'))

        # Check if OTP matches
        if otp_record.otp_code != form.otp.data:
            flash('Invalid OTP. Please try again.', 'danger')
            return redirect(url_for('verify_login_otp', email=email))

        # Mark OTP as verified
        otp_record.is_verified = True

        # Find the patient with this email
        patient = Patient.query.filter_by(email=email).first()

        if not patient:
            flash('Patient record not found.', 'danger')
            return redirect(url_for('patient_gmail_login'))

        # Login the patient
        login_user(patient)

        try:
            db.session.commit()

            # If this is the patient's first login with Gmail,
            # they might need to complete their profile
            if not patient.is_registered:
                flash('Please complete your profile information.', 'info')
                # Here we would ideally redirect to a profile completion page
                # For now, we'll just go to the dashboard

            return redirect(url_for('patient_dashboard'))

        except Exception as e:
            db.session.rollback()
            flash(f'Error verifying OTP: {str(e)}', 'danger')

    return render_template('patient/verify_login_otp.html', form=form, email=email)


@app.route('/patient/login', methods=['GET', 'POST'])
def patient_login():
    """Patient login route"""
    # If already logged in, redirect to patient dashboard
    if current_user.is_authenticated:
        return redirect(url_for('patient_dashboard'))

    form = PatientLoginForm()
    if form.validate_on_submit():
        try:
            patient = Patient.query.filter_by(email=form.email.data).first()

            # Check if patient exists and password is correct
            if patient and patient.is_registered and patient.check_password(form.password.data):
                login_user(patient)
                flash('Login successful!', 'success')
                return redirect(url_for('patient_dashboard'))
            else:
                flash('Invalid email or password', 'danger')
        except Exception as e:
            print(f"Login error: {str(e)}")
            flash('An error occurred during login. Please try again.', 'danger')

    return render_template('patient/login.html', form=form)


@app.route('/patient/logout')
@login_required
def patient_logout():
    """Patient logout route"""
    logout_user()
    flash('You have been logged out', 'info')
    return redirect(url_for('index'))


@app.route('/patient/dashboard')
@login_required
def patient_dashboard():
    """Patient dashboard route"""
    # Get patient's appointments
    appointments = Appointment.query.filter_by(patient_id=current_user.id).order_by(desc(Appointment.appointment_date), desc(Appointment.appointment_time)).all()

    return render_template('patient/dashboard.html', appointments=appointments)


@app.route('/patient/appointments')
@login_required
def patient_appointments():
    """Patient appointments history route"""
    # Get patient's appointments
    appointments = Appointment.query.filter_by(patient_id=current_user.id).order_by(desc(Appointment.appointment_date)).all()
    # Create a minimal form for CSRF
    form = FlaskForm()
    return render_template('patient/appointments.html', appointments=appointments, form=form)

@app.route('/patient/cancel-appointment/<int:appointment_id>', methods=['POST'])
@login_required
def patient_cancel_appointment(appointment_id):
    """Patient appointment cancellation route"""
    appointment = Appointment.query.get_or_404(appointment_id)

    # Verify this appointment belongs to the current user
    if appointment.patient_id != current_user.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('patient_appointments'))

    # Check if appointment is within 24 hours
    if datetime.now() + timedelta(hours=24) > datetime.combine(appointment.appointment_date, appointment.appointment_time):
        flash('Appointments can only be cancelled at least 24 hours before the scheduled time.', 'warning')
        return redirect(url_for('patient_appointments'))

    if appointment.status != 'scheduled':
        flash('Only scheduled appointments can be cancelled.', 'warning')
        return redirect(url_for('patient_appointments'))

    try:
        appointment.status = 'cancelled'
        db.session.commit()

        # Send email notification to clinic and patient
        clinic_message = f"""
        Appointment Cancellation Notice

        Patient: {appointment.patient.full_name}
        Date: {appointment.appointment_date}
        Time: {appointment.appointment_time}

        The appointment has been cancelled by the patient.
        """
        patient_message = f"""
        Dear {appointment.patient.full_name},

        Your appointment scheduled for {appointment.appointment_date.strftime('%d %B, %Y')} at {appointment.appointment_time.strftime('%I:%M %p')} has been cancelled.  We apologize for any inconvenience.

        Best regards,
        Dr. Richa's Eye Clinic
        """
        send_email_notification(app.config['MAIL_USERNAME'], "Appointment Cancellation", clinic_message)
        send_email_notification(appointment.patient.email, "Appointment Cancellation", patient_message)

        flash('Appointment cancelled successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error cancelling appointment: {str(e)}', 'danger')

    return redirect(url_for('patient_appointments'))


@app.route('/patient/medical-records')
@login_required
def patient_medical_records():
    """Patient medical records route"""
    # Get patient's appointments with medical records
    appointments = (
        db.session.query(Appointment)
        .join(MedicalRecord, Appointment.id == MedicalRecord.appointment_id)
        .filter(Appointment.patient_id == current_user.id)
        .order_by(desc(Appointment.appointment_date))
        .all()
    )

    return render_template('patient/medical_records.html', appointments=appointments)


# Authentication Selection Route
@app.route('/auth/selection')
def auth_selection():
    """Authentication selection route for choosing between staff and patient login"""
    return render_template('auth/selection.html')


# Doctor Authentication Routes
@app.route('/doctor/login', methods=['GET', 'POST'])
def doctor_login():
    """Doctor login route"""
    form = DoctorLoginForm()

    if form.validate_on_submit():
        # Get the doctor with username 'drricha'
        doctor = Doctor.query.filter_by(username='drricha').first()

        if doctor and doctor.check_password(form.password.data):
            login_user(doctor)
            # Set session variable to indicate doctor role
            session['user_role'] = 'doctor'
            flash('Welcome back, Dr. Richa!', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid credentials. Please check your username and password.', 'danger')

    return render_template('doctor/login.html', form=form)


@app.route('/doctor/logout')
@login_required
def doctor_logout():
    """Doctor logout route"""
    if current_user.is_authenticated and isinstance(current_user, Doctor):
        logout_user()
        flash('You have been logged out.', 'info')

    return redirect(url_for('auth_selection'))


# Assistant Authentication Routes
@app.route('/assistant/login', methods=['GET', 'POST'])
def assistant_login():
    """Assistant login route"""
    # If already logged in as assistant, redirect to dashboard
    if current_user.is_authenticated:
        if isinstance(current_user, Assistant):
            return redirect(url_for('assistant_dashboard'))
        logout_user()

    form = AssistantLoginForm()
    if form.validate_on_submit():
        # Find assistant with this username
        assistant = Assistant.query.filter_by(username=form.username.data).first()

        if assistant and assistant.check_password(form.password.data):
            login_user(assistant)
            session['user_role'] = 'assistant'  # Set role in session
            flash('Login successful! Welcome, ' + assistant.full_name, 'success')
            return redirect(url_for('assistant_dashboard'))
        else:
            flash('Invalid username or password.', 'danger')

    return render_template('assistant/login.html', form=form)


@app.route('/assistant/logout')
@login_required
def assistant_logout():
    """Assistant logout route"""
    if current_user.is_authenticated and isinstance(current_user, Assistant):
        logout_user()
        flash('You have been logged out.', 'info')

    return redirect(url_for('auth_selection'))


@app.route('/assistant/dashboard')
@login_required
def assistant_dashboard():
    """Assistant/Optometrist dashboard route"""
    if not isinstance(current_user, Assistant):
        flash('You do not have permission to access this page.', 'danger')
        return redirect(url_for('index'))

    try:
        # Get statistics
        today = datetime.now().date()
        upcoming_appointments = Appointment.query.filter(
            Appointment.appointment_date >= today,
            Appointment.status == 'scheduled'
        ).count()

        total_appointments = Appointment.query.count()
        total_patients = Patient.query.count()
        prescriptions_count = OptometristPrescription.query.filter_by(assistant_id=current_user.id).count()

        # Get salary records
        salary_records = Salary.query.filter_by(
            assistant_id=current_user.id
        ).order_by(desc(Salary.payment_date)).all()

        return render_template(
            'assistant/optometrist_dashboard.html',
            upcoming_appointments=upcoming_appointments,
            total_appointments=total_appointments,
            total_patients=total_patients,
            prescriptions_count=prescriptions_count,
            salary_records=salary_records
        )
    except Exception as e:
        flash(f'Error loading dashboard: {str(e)}', 'danger')
        return redirect(url_for('index'))

    try:
        # Create form for CSRF token
        form = FlaskForm()

        # Get all patients
        all_patients = Patient.query.order_by(Patient.full_name).all()

        # Get today's appointments
        today = datetime.now().date()
        today_appointments = Appointment.query.filter_by(appointment_date=today).all()

        # Get all appointments
        all_appointments = Appointment.query.order_by(desc(Appointment.appointment_date)).all()

        # Get upcoming appointments count
        upcoming_appointments = Appointment.query.filter(
            Appointment.appointment_date >= today,
            Appointment.status == 'scheduled'
        ).count()

        # Get total appointments
        total_appointments = Appointment.query.count()

        # Get total patients
        total_patients = Patient.query.count()

        # Get salary records
        salary_records = Salary.query.filter_by(assistant_id=current_user.id).order_by(desc(Salary.payment_date)).all()

        return render_template(
            'assistant/dashboard.html',
            form=form,
            all_patients=all_patients,
            today_appointments=today_appointments,
            all_appointments=all_appointments,
            upcoming_appointments=upcoming_appointments,
            total_appointments=total_appointments,
            total_patients=total_patients,
            salary_records=salary_records
        )
    except Exception as e:
        flash(f'Error loading dashboard: {str(e)}', 'danger')
        return redirect(url_for('index'))

    try:
        # Get all patients
        all_patients = db.session.query(
            Patient.id, 
            Patient.full_name, 
            Patient.mobile_number, 
            Patient.email, 
            Patient.age, 
            Patient.is_registered
        ).all()

        # Get today's appointments
        today = datetime.now().date()
        today_appointments = Appointment.query.filter_by(appointment_date=today).all()

        # Get all appointments
        all_appointments = Appointment.query.order_by(desc(Appointment.appointment_date)).all()

        # Get upcoming appointments
        upcoming_appointments = Appointment.query.filter(
            Appointment.appointment_date >= today,
            Appointment.status == 'scheduled'
        ).count()

        # Get total appointments
        total_appointments = Appointment.query.count()

        # Get total patients
        total_patients = Patient.query.count()

        # Get salary records for current assistant
        salary_records = Salary.query.filter_by(assistant_id=current_user.id).order_by(desc(Salary.payment_date)).all()
    except Exception as e:
        flash(f'Error loading dashboard data: {str(e)}', 'danger')
        return redirect(url_for('index'))

    return render_template(
        'assistant/dashboard.html',
        all_patients=all_patients,
        today_appointments=today_appointments,
        all_appointments=all_appointments,
        upcoming_appointments=upcoming_appointments,
        total_appointments=total_appointments,
        total_patients=total_patients,
        salary_records=salary_records
    )


# Admin/Doctor Authentication Routes
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """Admin login route"""
    # Check if user is already logged in as admin
    if current_user.is_authenticated and isinstance(current_user, Admin):
        return redirect(url_for('admin_dashboard'))

    form = AdminLoginForm()
    if form.validate_on_submit():
        admin = Admin.query.filter_by(username=form.username.data).first()

        # Check if admin exists and password is correct
        if admin and admin.check_password(form.password.data):
            login_user(admin)

            # Redirect to admin dashboard
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid username or password', 'danger')

    return render_template('admin/login.html', form=form)


@app.route('/admin/logout')
@login_required
def admin_logout():
    """Admin logout route"""
    logout_user()
    flash('You have been logged out', 'info')
    return redirect(url_for('index'))


@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    """Admin/Doctor dashboard route"""
    # Ensure only admins, doctors or assistants can access this page
    if not (isinstance(current_user, Admin) or isinstance(current_user, Doctor) or isinstance(current_user, Assistant)):
        flash('Access denied. Staff privileges required.', 'danger')
        return redirect(url_for('index'))

    # Get counts for dashboard
    total_patients = Patient.query.count()
    total_appointments = Appointment.query.count()
    upcoming_appointments = Appointment.query.filter(
        Appointment.appointment_date >= datetime.now().date(),
        Appointment.status == 'scheduled'
    ).count()
    pending_reviews = Review.query.filter_by(is_approved=False).count()

    # Today's appointments
    today_appointments = Appointment.query.filter(
        Appointment.appointment_date == datetime.now().date(),
        Appointment.status == 'scheduled'
    ).order_by(Appointment.appointment_time).all()

    return render_template('admin/dashboard.html', 
                          total_patients=total_patients,
                          total_appointments=total_appointments,
                          upcoming_appointments=upcoming_appointments,
                          pending_reviews=pending_reviews,
                          today_appointments=today_appointments)


@app.route('/admin/appointments')
@login_required
def admin_appointments():
    """Admin appointments management route"""
    # Ensure only admins, doctors or assistants can access this page
    if not (isinstance(current_user, Admin) or isinstance(current_user, Doctor) or isinstance(current_user, Assistant)):
        flash('Access denied. Staff privileges required.', 'danger')
        return redirect(url_for('index'))

    # Get all appointments
    appointments = Appointment.query.order_by(desc(Appointment.appointment_date), desc(Appointment.appointment_time)).all()

    return render_template('admin/appointments.html', appointments=appointments)


@app.route('/admin/patients')
@login_required
def admin_patients():
    """Admin patients management route"""
    # Ensure only admins, doctors or assistants can access this page
    if not (isinstance(current_user, Admin) or isinstance(current_user, Doctor) or isinstance(current_user, Assistant)):
        flash('Access denied. Staff privileges required.', 'danger')
        return redirect(url_for('index'))

    # Get all patients
    patients = Patient.query.order_by(Patient.full_name).all()

    return render_template('admin/patients.html', patients=patients)


@app.route('/admin/patient/<int:patient_id>')
@login_required
def admin_patient_view(patient_id):
    """Admin patient view route"""
    # Ensure only admins or assistants can access this page
    if not (isinstance(current_user, Admin) or isinstance(current_user, Assistant) or isinstance(current_user, Doctor)):
        flash('Access denied. Staff privileges required.', 'danger')
        return redirect(url_for('index'))

    # Set return URL based on user role
    if isinstance(current_user, Assistant):
        return_url = url_for('assistant_dashboard')
    elif isinstance(current_user, Doctor):
        return_url = url_for('admin_dashboard')
    else:
        return_url = url_for('admin_dashboard')

    # Get patient details
    patient = Patient.query.get_or_404(patient_id)

    # Get patient's appointments and medical records
    appointments = Appointment.query.filter_by(patient_id=patient_id).order_by(desc(Appointment.appointment_date)).all()

    return render_template('admin/patient_view.html', patient=patient, appointments=appointments)


@app.route('/admin/appointment/<int:appointment_id>', methods=['GET', 'POST'])
@login_required
def admin_appointment_view(appointment_id):
    """Admin appointment view route"""
    # Ensure only admins or assistants can access this page
    if not (isinstance(current_user, Admin) or isinstance(current_user, Assistant) or isinstance(current_user, Doctor)):
        flash('Access denied. Staff privileges required.', 'danger')
        return redirect(url_for('index'))

    # Get appointment details
    appointment = Appointment.query.get_or_404(appointment_id)

    # Handle POST requests for updating appointment status
    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'complete':
            appointment.status = 'completed'
            message = "Your appointment has been completed. Thank you for visiting Dr. Richa's Eye Clinic."

            try:
                db.session.commit()

                # Send email notification if patient has email
                if appointment.patient.email:
                    subject = f"Appointment {appointment.status.title()} - Dr. Richa's Eye Clinic"
                    send_email_notification(appointment.patient.email, subject, message)

                flash('Appointment marked as completed.', 'success')
                return redirect(url_for('admin_appointment_view', appointment_id=appointment_id))
            except Exception as e:
                db.session.rollback()
                flash(f'Error updating appointment:: {str(e)}', 'danger')

        elif action == 'cancel':
            appointment.status = 'cancelled'
            message = "Your appointment has been cancelled. Please contact us if you need to reschedule."

            try:
                db.session.commit()

                # Send email notification if patient has email
                if appointment.patient.email:
                    subject = f"Appointment {appointment.status.title()} - Dr. Richa's Eye Clinic"
                    send_email_notification(appointment.patient.email, subject, message)

                flash('Appointment has been cancelled.', 'warning')
                return redirect(url_for('admin_appointment_view', appointment_id=appointment_id))
            except Exception as e:
                db.session.rollback()
                flash(f'Error updating appointment: {str(e)}', 'danger')

    # Get medical record if it exists
    medical_record = MedicalRecord.query.filter_by(appointment_id=appointment_id).first()
    has_medical_record = medical_record is not None

    return render_template('admin/appointment_view.html', appointment=appointment, medical_record=medical_record, has_medical_record=has_medical_record)

@app.route('/admin/prescription/<int:appointment_id>', methods=['GET', 'POST'])
@login_required
def admin_add_prescription(appointment_id):
    """Admin add/edit prescription route"""
    # Ensure only admins or assistants can access this page
    if not (isinstance(current_user, Admin) or isinstance(current_user, Assistant) or isinstance(current_user, Doctor)):
        flash('Access denied. Staff privileges required.', 'danger')
        return redirect(url_for('index'))

    # Get appointment details
    appointment = Appointment.query.get_or_404(appointment_id)
    print(f"Found appointment for patient ID: {appointment.patient_id}")  # Debug log

    # Get or create medical record
    medical_record = MedicalRecord.query.filter_by(appointment_id=appointment_id).first()
    is_edit = medical_record is not None

    if not medical_record:
        medical_record = MedicalRecord(appointment_id=appointment_id)
        db.session.add(medical_record)
        db.session.flush()
        print("Created new medical record")  # Debug log

    form = PrescriptionForm(obj=medical_record)

    if form.validate_on_submit():
        print("Form validated successfully")  # Debug log
        # Update medical record with form data
        form.populate_obj(medical_record)
        print(f"Medical record updated with diagnosis: {form.diagnosis.data}")  # Debug log

        try:
            # Get the default doctor (Dr. Richa)
            doctor = Doctor.query.filter_by(username='drricha').first()
            if not doctor:
                print("Default doctor not found, creating one...")
                doctor = Doctor(
                    username='drricha',
                    email='drricha@eyeclinic.com',
                    full_name='Dr. Richa',
                    mobile_number='0000000000'
                )
                doctor.set_password('default_password')
                db.session.add(doctor)
                db.session.flush()
                print(f"Created default doctor with ID: {doctor.id}")

            # Create a DoctorPrescription record
            doctor_prescription = DoctorPrescription(
                patient_id=appointment.patient_id,
                doctor_id=doctor.id,  # Always use the default doctor's ID
                prescription_date=datetime.utcnow(),
                diagnosis=form.diagnosis.data,
                medications=form.prescribed_medications.data,
                instructions=form.follow_up_instructions.data,
                follow_up=form.next_appointment_recommendation.data
            )
            print(f"Created doctor prescription for patient {appointment.patient_id} with doctor {doctor.id}")  # Debug log
            db.session.add(doctor_prescription)

            # Update appointment status to completed
            appointment.status = 'completed'

            db.session.commit()
            print("Successfully committed changes to database")  # Debug log

            # Verify the prescription was saved
            saved_prescription = DoctorPrescription.query.filter_by(
                patient_id=appointment.patient_id,
                doctor_id=doctor.id
            ).order_by(DoctorPrescription.created_at.desc()).first()

            if saved_prescription:
                print(f"Verified prescription saved with ID: {saved_prescription.id}")
            else:
                print("Warning: Could not verify prescription was saved")

            if is_edit:
                flash('Prescription updated successfully!', 'success')
            else:
                flash('Prescription added successfully!', 'success')
            return redirect(url_for('admin_appointment_view', appointment_id=appointment_id))
        except Exception as e:
            db.session.rollback()
            print(f"Error saving prescription: {str(e)}")  # Debug log
            flash(f'Error saving prescription: {str(e)}', 'danger')

    return render_template('admin/add_prescription.html', form=form, appointment=appointment, is_edit=is_edit)


@app.route('/admin/assistant-salary', methods=['GET', 'POST'])
@login_required
def admin_assistant_salary():
    """Doctor's route to manage assistant salaries"""
    if not isinstance(current_user, Doctor):
        flash('Access denied. Doctor privileges required.', 'danger')
        return redirect(url_for('index'))

    form = SalaryForm()
    if form.validate_on_submit():
        # Get the default assistant account
        assistant = Assistant.query.filter_by(email='assistant@eyeclinic.com').first()
        if assistant:
            try:
                # Create salary record
                new_salary = Salary(
                    assistant_id=assistant.id,
                    amount=float(form.amount.data),
                    payment_date=form.payment_date.data,
                    payment_method=form.payment_method.data,
                    description=form.description.data,
                    status='completed'
                )
                db.session.add(new_salary)
                db.session.commit()

                # Send email notification
                subject = "Salary Payment Receipt - Dr. Richa's Eye Clinic"
                message = f"""
            Dear Optrometrist,

            Your salary payment has been processed:

            Amount: ₹{form.amount.data}
            Date: {form.payment_date.data}
            Payment Method: {form.payment_method.data}
            Description: {form.description.data}

            Best regards,
            Dr. Richa's Eye Clinic
            """
                send_email_notification('assistant@eyeclinic.com', subject, message)
                flash('Salary payment processed successfully!', 'success')
                return redirect(url_for('admin_assistant_salary'))
            except Exception as e:
                db.session.rollback()
                flash(f'Error processing salary: {str(e)}', 'danger')
                return redirect(url_for('admin_assistant_salary'))
        else:
            flash('Assistant not found', 'danger')

    # Get all salary records
    assistant = Assistant.query.filter_by(email='assistant@eyeclinic.com').first()
    salary_records = Salary.query.filter_by(assistant_id=assistant.id).order_by(desc(Salary.payment_date)).all() if assistant else []

    return render_template('admin/assistant_salary.html', form=form, salary_records=salary_records)

@app.route('/admin/reviews')
@login_required
def admin_reviews():
    """Admin reviews management route"""
    # Ensure only admins, doctors or assistants can access this page
    if not (isinstance(current_user, Admin) or isinstance(current_user, Doctor) or isinstance(current_user, Assistant)):
        flash('Access denied. Staff privileges required.', 'danger')
        return redirect(url_for('index'))

    # Get pending reviews
    pending_reviews = Review.query.filter_by(is_approved=False).order_by(desc(Review.created_at)).all()

    # Get approved reviews
    approved_reviews = Review.query.filter_by(is_approved=True).order_by(desc(Review.created_at)).all()

    return render_template('admin/reviews.html', pending_reviews=pending_reviews, approved_reviews=approved_reviews)


@app.route('/admin/review/approve/<int:review_id>', methods=['POST'])
@login_required
def admin_approve_review(review_id):
    """Admin approve review route"""
    # Ensure only admins or assistants can access this page
    if not (isinstance(current_user, Admin) or isinstance(current_user, Doctor) or isinstance(current_user, Assistant)):
        flash('Access denied. Staff privileges required.', 'danger')
        return redirect(url_for('index'))

    # Get review
    review = Review.query.get_or_404(review_id)

    # Approve review
    review.is_approved = True

    try:
        db.session.commit()
        flash('Review approved!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error approving review: {str(e)}', 'danger')

    return redirect(url_for('admin_reviews'))

@app.route('/admin/review/delete/<int:review_id>', methods=['POST'])
@login_required
def admin_delete_review(review_id):
    """Admin delete review route"""
    # Ensure only admins or assistants can access this page
    if not (isinstance(current_user, Admin) or isinstance(current_user, Doctor) or isinstance(current_user, Assistant)):
        flash('Access denied. Staff privileges required.', 'danger')
        return redirect(url_for('index'))

    # Get review
    review = Review.query.get_or_404(review_id)

    try:
        db.session.delete(review)
        db.session.commit()
        flash('Review deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting review: {str(e)}', 'danger')

    return redirect(url_for('admin_reviews'))

def send_email_notification(to_email, subject, message):
    try:
        smtp_server = app.config['MAIL_SERVER']
        smtp_port = app.config['MAIL_PORT']
        sender_email = app.config['MAIL_USERNAME']
        sender_password = app.config['MAIL_PASSWORD']

        # Create message
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(message, 'plain'))

        # Send email
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)
        return True
    except Exception as e:
        print(f"Error sending email: {str(e)}")
        return False

@app.route('/assistant/add-patient', methods=['GET', 'POST'])
@login_required
def assistant_add_patient():
    if not isinstance(current_user, Assistant):
        flash('Access denied.', 'danger')
        return redirect(url_for('index'))

    form = PatientRegistrationForm()
    if form.validate_on_submit():
        try:
            # Create new patient
            new_patient = Patient(
                full_name=form.full_name.data,
                mobile_number=form.mobile_number.data,
                email=form.email.data,
                age=form.age.data,
                sex=form.sex.data,
                is_registered=False
            )
            db.session.add(new_patient)
            db.session.flush()  # Get patient ID

            # Create walk-in appointment for today
            today = datetime.now().date()
            current_time = datetime.now().time()

            walk_in_appointment = Appointment(
                patient_id=new_patient.id,
                appointment_date=today,
                appointment_time=current_time,
                primary_issue=form.primary_issue.data or "Walk-in consultation",
                status='completed',  # Mark as completed since it's walk-in
                consultation_fee=500.0,
                payment_status='paid'
            )
            db.session.add(walk_in_appointment)
            db.session.flush()  # Get appointment ID

            # Create payment record for revenue tracking
            walk_in_payment = Payment(
                appointment_id=walk_in_appointment.id,
                amount=500.0,
                payment_method='cash',
                status='completed'
            )
            db.session.add(walk_in_payment)

            # Create treatment record for revenue tracking
            walk_in_treatment = Treatment(
                patient_id=new_patient.id,
                treatment_name='Walk-in Consultation',
                treatment_date=today,
                amount=500.0,
                notes=f'Walk-in patient added by {current_user.full_name}'
            )
            db.session.add(walk_in_treatment)

            db.session.commit()
            flash('Walk-in patient added successfully and ₹500 consultation fee recorded!', 'success')
            return redirect(url_for('assistant_dashboard'))

        except Exception as e:
            db.session.rollback()
            flash(f'Error adding patient: {str(e)}', 'danger')
            print(f"Error adding walk-in patient: {str(e)}")

    return render_template('assistant/add_patient.html', form=form)



@app.route('/doctor/prescriptions')
@login_required
def doctor_prescriptions():
    if not isinstance(current_user, Doctor):
        flash('Access denied', 'danger')
        return redirect(url_for('index'))

    all_patients = Patient.query.order_by(Patient.full_name).all()
    return render_template('doctor/prescriptions.html', all_patients=all_patients)

@app.route('/doctor/add-prescription/<int:patient_id>', methods=['GET', 'POST'])
@login_required
def doctor_add_prescription(patient_id):
    from forms import DoctorPrescriptionForm
    from models import Patient, DoctorPrescription, Doctor
    from datetime import datetime

    patient = Patient.query.get_or_404(patient_id)
    form = DoctorPrescriptionForm()

    if form.validate_on_submit():
        try:
            # Get the current doctor
            doctor = Doctor.query.filter_by(username='drricha').first()
            if not doctor:
                flash('Doctor not found', 'error')
                return redirect(url_for('doctor_prescriptions'))

            # Create comprehensive prescription with all fields
            prescription = DoctorPrescription(
                patient_id=patient_id,
                doctor_id=doctor.id,
                # Clinical information
                complaints=form.complaints.data,
                history=form.history.data,
                examination_notes=form.examination_notes.data,
                diagnosis=form.diagnosis.data,
                # Eye examination findings
                left_eye_findings=form.left_eye_findings.data,
                right_eye_findings=form.right_eye_findings.data,
                # Investigation and assessment
                investigation=form.investigation.data,
                fall_risk=form.fall_risk.data,
                immunization=form.immunization.data,
                # Treatment plan
                medications=form.medications.data,
                prognosis=form.prognosis.data,
                nutritional_advice=form.nutritional_advice.data,
                plan_of_care=form.plan_of_care.data,
                # Instructions and follow-up
                instructions=form.instructions.data,
                follow_up=form.follow_up.data,
                referral_reason=form.referral_reason.data,
                referred_to_cc=form.referred_to_cc.data,
                # Additional notes
                comments=form.comments.data,
                remarks_for_counselor=form.remarks_for_counselor.data
            )

            db.session.add(prescription)
            db.session.commit()

            flash('Comprehensive prescription saved successfully!', 'success')
            return redirect(url_for('doctor_prescriptions'))

        except Exception as e:
            db.session.rollback()
            flash(f'Error saving prescription: {str(e)}', 'error')

    return render_template('doctor/add_prescription.html', 
                         form=form, 
                         patient=patient,
                         now=datetime.utcnow())

@app.route('/assistant/prescriptions')
@login_required
def assistant_prescriptions():
    if not isinstance(current_user, Assistant):
        flash('Access denied', 'danger')
        return redirect(url_for('index'))

    all_patients = Patient.query.order_by(Patient.full_name).all()
    return render_template('assistant/prescriptions.html', all_patients=all_patients)

@app.route('/assistant/add-prescription/<int:patient_id>', methods=['GET', 'POST'])
@login_required
def assistant_add_prescription(patient_id):
    if not isinstance(current_user, Assistant):
        flash('Access denied', 'danger')
        return redirect(url_for('index'))

    form = OptometristPrescriptionForm()
    patient = Patient.query.get_or_404(patient_id)

    if form.validate_on_submit():
        prescription = OptometristPrescription(
            patient_id=patient_id,
            assistant_id=current_user.id,
            vision_test=form.vision_test.data,
            eye_power=form.eye_power.data,
            recommendations=form.recommendations.data,
            notes=form.notes.data
        )
        db.session.add(prescription)
        try:
            db.session.commit()
            flash('Prescription added successfully', 'success')
            return redirect(url_for('assistant_prescriptions'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding prescription: {str(e)}', 'danger')

    return render_template('assistant/add_prescription.html', form=form, patient=patient)

@app.route('/print-prescription/<string:type>/<int:prescription_id>')
@login_required
def print_prescription(type, prescription_id):
    """Print prescription route"""
    # Ensure only staff members can access this page
    if not (isinstance(current_user, Doctor) or isinstance(current_user, Assistant) or isinstance(current_user, Admin)):
        flash('Access denied. Staff privileges required.', 'danger')
        return redirect(url_for('index'))

    if type == 'doctor':
        prescription = DoctorPrescription.query.get_or_404(prescription_id)
        template = 'doctor/print_prescription.html'
    elif type == 'optometrist':
        prescription = OptometristPrescription.query.get_or_404(prescription_id)
        template = 'assistant/print_prescription.html'
    else:
        flash('Invalid prescription type', 'danger')
        return redirect(url_for('index'))

    return render_template(template, prescription=prescription)

@app.route('/admin/revenue', methods=['GET', 'POST'])
@login_required
def admin_revenue():
    """Revenue management route"""
    if not isinstance(current_user, Doctor):
        flash('Access denied. Doctor privileges required.', 'danger')
        return redirect(url_for('index'))

    form = FlaskForm()  # Create a basic form for CSRF protection

    if request.method == 'POST':
        try:
            new_treatment = Treatment(
                patient_id=request.form.get('patient_id'),
                treatment_name=request.form.get('treatment_name'),
                treatment_date=datetime.strptime(request.form.get('treatment_date'), '%Y-%m-%d').date(),
                amount=float(request.form.get('amount')),
                notes=request.form.get('notes')
            )
            db.session.add(new_treatment)
            db.session.commit()
            flash('Treatment record added successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding treatment: {str(e)}', 'danger')

    # Get all payments with patient details
    payments = (
        db.session.query(Payment, Patient)
        .join(Appointment, Payment.appointment_id == Appointment.id)
        .join(Patient, Appointment.patient_id == Patient.id)
        .order_by(Payment.created_at.desc())
        .all()
    )

    # Get all treatments
    treatments = Treatment.query.order_by(Treatment.treatment_date.desc()).all()

    # Calculate total revenue
    appointment_revenue = sum(payment.amount for payment, _ in payments if payment.status == 'completed')
    treatment_revenue = sum(treatment.amount for treatment in treatments)
    total_revenue = appointment_revenue + treatment_revenue

    # Get all patients for the treatment form
    patients = Patient.query.order_by(Patient.full_name).all()

    return render_template('admin/revenue.html', payments=payments, treatments=treatments, patients=patients, total_revenue=total_revenue, form=form)

@app.route('/print-combined-prescription/<int:patient_id>')
@login_required
def print_combined_prescription(patient_id):
    """Print combined doctor and optometrist prescriptions route"""
    # Ensure only staff members can access this page
    if not (isinstance(current_user, Doctor) or isinstance(current_user, Assistant) or isinstance(current_user, Admin)):
        flash('Access denied. Staff privileges required.', 'danger')
        return redirect(url_for('index'))

    # Get patient
    patient = Patient.query.get_or_404(patient_id)

    # Get latest doctor prescription
    doctor_prescription = DoctorPrescription.query.filter_by(
        patient_id=patient_id
    ).order_by(DoctorPrescription.created_at.desc()).first()

    # Get latest optometrist prescription
    optometrist_prescription = OptometristPrescription.query.filter_by(
        patient_id=patient_id
    ).order_by(OptometristPrescription.created_at.desc()).first()

    if not doctor_prescription and not optometrist_prescription:
        flash('No prescriptions found for this patient.', 'warning')
        return redirect(url_for('admin_patient_view', patient_id=patient_id))

    return render_template('print_combined_prescription.html',
                         patient=patient,
                         doctor_prescription=doctor_prescription,
                         optometrist_prescription=optometrist_prescription)

@app.route('/delete-prescription/<string:type>/<int:prescription_id>', methods=['POST'])
@login_required
def delete_prescription(type, prescription_id):
    """Delete prescription route"""
    # Ensure only staff members can access this page
    if not (isinstance(current_user, Doctor) or isinstance(current_user, Assistant) or isinstance(current_user, Admin)):
        flash('Access denied. Staff privileges required.', 'danger')
        return redirect(url_for('index'))

    print(f"Delete prescription request: type={type}, id={prescription_id}")  # Debug log
    try:
        if type == 'doctor':
            prescription = DoctorPrescription.query.get_or_404(prescription_id)
            prescription_type = "Doctor"
            redirect_route = 'doctor_prescriptions' if isinstance(current_user, Doctor) else 'admin_dashboard'
        elif type == 'optometrist':
            prescription = OptometristPrescription.query.get_or_404(prescription_id)
            prescription_type = "Optometrist"
            redirect_route = 'assistant_prescriptions' if isinstance(current_user, Assistant) else 'admin_dashboard'
        else:
            flash('Invalid prescription type', 'danger')
            return redirect(url_for('admin_dashboard'))

        # Store patient info for redirect if needed
        patient_id = prescription.patient_id

        # Delete the prescription
        db.session.delete(prescription)
        db.session.commit()

        flash(f'{prescription_type} prescription deleted successfully!', 'success')

        # Check where to redirect based on referer
        referer = request.referrer
        if referer and 'patient_view' in referer:
            return redirect(url_for('admin_patient_view', patient_id=patient_id))
        elif isinstance(current_user, Doctor) and type == 'doctor':
            return redirect(url_for('doctor_prescriptions'))
        elif isinstance(current_user, Assistant) and type == 'optometrist':
            return redirect(url_for('assistant_prescriptions'))
        else:
            return redirect(url_for('admin_dashboard'))

    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting prescription: {str(e)}', 'danger')
        return redirect(request.referrer or url_for('admin_dashboard'))

@app.route('/patient/google-login')
def patient_google_login():
    """Patient Google OAuth login route"""
    # If already logged in, redirect to patient dashboard
    if current_user.is_authenticated:
        return redirect(url_for('patient_dashboard'))

    # Generate OAuth URL
    oauth_url = "https://accounts.google.com/o/oauth2/v2/auth"
    client_id = "your-client-id"  # Replace with your Google OAuth client ID
    redirect_uri = url_for('patient_google_callback', _external=True)
    scope = "email profile"
    state = ''.join(random.choices(string.ascii_letters + string.digits, k=32))
    session['oauth_state'] = state

    auth_url = f"{oauth_url}?client_id={client_id}&redirect_uri={redirect_uri}&response_type=code&scope={scope}&state={state}"
    return redirect(auth_url)

@app.route('/patient/google-callback')
def patient_google_callback():
    """Google OAuth callback route"""
    if 'error' in request.args:
        flash('Google login failed. Please try again.', 'danger')
        return redirect(url_for('patient_login'))

    if request.args.get('state') != session.get('oauth_state'):
        flash('Invalid state parameter. Please try again.', 'danger')
        return redirect(url_for('patient_login'))

    code = request.args.get('code')
    if not code:
        flash('No authorization code received.', 'danger')
        return redirect(url_for('patient_login'))

    try:
        # Exchange code for tokens
        token_url = "https://oauth2.googleapis.com/token"
        client_id = "your-client-id"  # Replace with your Google OAuth client ID
        client_secret = "your-client-secret"  # Replace with your Google OAuth client secret
        redirect_uri = url_for('patient_google_callback', _external=True)

        token_data = {
            'code': code,
            'client_id': client_id,
            'client_secret': client_secret,
            'redirect_uri': redirect_uri,
            'grant_type': 'authorization_code'
        }

        token_response = requests.post(token_url, data=token_data)
        token_response.raise_for_status()
        tokens = token_response.json()

        # Get user info
        userinfo_url = "https://www.googleapis.com/oauth2/v2/userinfo"
        headers = {'Authorization': f"Bearer {tokens['access_token']}"}
        userinfo_response = requests.get(userinfo_url, headers=headers)
        userinfo_response.raise_for_status()
        userinfo = userinfo_response.json()

        # Find or create patient
        patient = Patient.query.filter_by(email=userinfo['email']).first()
        if not patient:
            patient = Patient(
                full_name=userinfo.get('name', 'Google User'),
                email=userinfo['email'],
                mobile_number='0000000000',  # Will be updated later
                age=1,  # Will be updated later
                is_registered=False
            )
            db.session.add(patient)
            db.session.commit()

        # Login the patient
        login_user(patient)
        flash('Successfully logged in with Google!', 'success')
        return redirect(url_for('patient_dashboard'))

    except Exception as e:
        flash(f'Error during Google login: {str(e)}', 'danger')
        return redirect(url_for('patient_login'))