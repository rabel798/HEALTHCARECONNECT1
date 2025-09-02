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
    AppointmentForm, PaymentForm, ReviewForm, DoctorLoginForm, AssistantLoginForm, AdminLoginForm, PatientLoginForm, PatientRegistrationForm, OTPVerificationForm, PrescriptionForm, DoctorPrescriptionForm, OptometristPrescriptionForm, SalaryForm, FindAppointmentForm, ProfileCompletionForm, PatientEditForm
)
import requests
from urllib.parse import urlencode

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

    if form.validate_on_submit():
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
            # Store appointment ID and details in session for payment and success pages
            session['appointment_id'] = new_appointment.id
            session['appointment_details'] = {
                'patient_name': patient.full_name,
                'appointment_date': new_appointment.appointment_date.strftime('%A, %B %d, %Y'),
                'appointment_time': new_appointment.appointment_time.strftime('%I:%M %p')
            }

            # Send appointment application email
            subject = "Appointment Application Submitted - Dr. Richa's Eye Clinic"
            message = f"""
            Dear {patient.full_name},

            Thank you for submitting your appointment application. Your request has been received and is pending confirmation from our medical team.

            Appointment Details:
            - Date: {new_appointment.appointment_date.strftime('%d %B, %Y')}
            - Time: {new_appointment.appointment_time.strftime('%I:%M %p')}
            - Primary Issue: {new_appointment.primary_issue}

            We will send you a confirmation email once your appointment is approved by Dr. Richa.

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
    appointment_details = session.get('appointment_details', {})
    return render_template('success.html', appointment_details=appointment_details)



@app.route('/staff/verify-appointment', methods=['GET', 'POST'])
@login_required
def staff_verify_appointment():
    """Staff verification of appointments using confirmation number or patient details"""
    # Ensure only staff members can access this page
    if not (isinstance(current_user, Doctor) or isinstance(current_user, Assistant) or isinstance(current_user, Admin)):
        flash('Access denied. Staff privileges required.', 'danger')
        return redirect(url_for('index'))

    class VerifyAppointmentForm(FlaskForm):
        mobile_number = StringField('Mobile Number')
        email = StringField('Email')
        appointment_date = StringField('Appointment Date (YYYY-MM-DD)')
        submit = SubmitField('Search Appointment')

    form = VerifyAppointmentForm()
    appointment = None
    verification_result = None

    if form.validate_on_submit():
        # Search by patient details
        query = Appointment.query.join(Patient)

        if form.mobile_number.data:
            query = query.filter(Patient.mobile_number == form.mobile_number.data)
        if form.email.data:
            query = query.filter(Patient.email == form.email.data)
        if form.appointment_date.data:
            try:
                search_date = datetime.strptime(form.appointment_date.data, '%Y-%m-%d').date()
                query = query.filter(Appointment.appointment_date == search_date)
            except ValueError:
                verification_result = {
                    'status': 'invalid',
                    'message': 'Invalid date format. Use YYYY-MM-DD'
                }
                return render_template('staff/verify_appointment.html', form=form, verification_result=verification_result)

        appointment = query.first()
        if appointment:
            verification_result = {
                'status': 'found',
                'message': f'Appointment found for {appointment.patient.full_name}'
            }
        else:
            verification_result = {
                'status': 'not_found',
                'message': 'No appointment found with the provided details'
            }

    return render_template('staff/verify_appointment.html', 
                         form=form, 
                         appointment=appointment, 
                         verification_result=verification_result)

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

        # Get all non-cancelled appointments for the selected date
        booked_appointments = Appointment.query.filter_by(
            appointment_date=selected_date
        ).filter(Appointment.status != 'cancelled').all()

        # Count appointments per time slot
        slot_counts = {}
        for appointment in booked_appointments:
            time_str = appointment.appointment_time.strftime('%H:%M')
            slot_counts[time_str] = slot_counts.get(time_str, 0) + 1

        # Filter out slots that have 3 or more appointments (full capacity)
        available_slots = []
        for slot in all_slots:
            appointments_in_slot = slot_counts.get(slot, 0)
            if appointments_in_slot < 3:  # Allow up to 3 appointments per slot
                available_slots.append(slot)

        return jsonify(available_slots)
    except Exception as e:
        return jsonify({"error": str(e)}), 400


# Patient Authentication Routes
@app.route('/patient/register', methods=['GET', 'POST'])
def patient_register():
    """Patient registration route - disabled"""
    flash('Patient registration is no longer available. Please book appointments directly.', 'info')
    return redirect(url_for('appointment'))

    form = PatientRegistrationForm()
    if form.validate_on_submit():
        try:
            # Check if email or mobile already exists (only check email if provided)
            query_filters = [Patient.mobile_number == form.mobile_number.data]
            if form.email.data:
                query_filters.append(Patient.email == form.email.data)

            existing_patient = Patient.query.filter(db.or_(*query_filters)).first()

            if existing_patient:
                if existing_patient.mobile_number == form.mobile_number.data:
                    flash('A patient with this mobile number already exists.', 'danger')
                else:
                    flash('A patient with this email already exists.', 'danger')
                return render_template('patient/register.html', form=form)

            # If email is provided, use OTP verification
            if form.email.data:
                # Generate 6-digit OTP
                otp_code = ''.join(random.choices(string.digits, k=6))
                expires_at = datetime.utcnow() + timedelta(minutes=30)

                # Store OTP in database
                new_otp = OTP(
                    email=form.email.data,
                    otp_code=otp_code,
                    expires_at=expires_at
                )
                db.session.add(new_otp)
                db.session.commit()

                # Store registration data in session
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
                    flash('Registration completed! Please proceed to login.', 'info')

                return redirect(url_for('verify_otp', email=form.email.data))

            else:
                # Direct registration without email verification
                new_patient = Patient(
                    full_name=form.full_name.data,
                    mobile_number=form.mobile_number.data,
                    email='',
                    age=form.age.data,
                    sex=form.sex.data,
                    is_registered=True
                )
                if form.password.data:
                    new_patient.set_password(form.password.data)

                db.session.add(new_patient)
                db.session.commit()

                login_user(new_patient)
                flash('Registration successful! Welcome to Dr. Richa\'s Eye Clinic.', 'success')
                return redirect(url_for('patient_dashboard'))

        except Exception as e:
            db.session.rollback()
            print(f"Registration error: {str(e)}")
            flash(f'Registration failed: {str(e)}', 'danger')

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
    """Patient Gmail OTP login route - disabled"""
    flash('Patient login is no longer available. Please book appointments directly.', 'info')
    return redirect(url_for('appointment'))

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

        # Login the patient with remember=True for session persistence
        login_user(patient, remember=True)

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
    """Patient login route - disabled"""
    flash('Patient login is no longer available. Please book appointments directly.', 'info')
    return redirect(url_for('appointment'))

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
def patient_dashboard():
    """Patient dashboard route - disabled"""
    flash('Patient dashboard is no longer available. Please contact the clinic directly.', 'info')
    return redirect(url_for('index'))


@app.route('/patient/appointments')
def patient_appointments():
    """Patient appointments history route - disabled"""
    flash('Patient appointment history is no longer available. Please contact the clinic directly.', 'info')
    return redirect(url_for('index'))

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

        # Update payment status to cancelled as well
        if appointment.payment:
            appointment.payment.status = 'cancelled'

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


@app.route('/patient/complete-profile', methods=['GET', 'POST'])
@login_required
def patient_complete_profile():
    """Patient profile completion route"""
    if not isinstance(current_user, Patient):
        flash('Access denied.', 'danger')
        return redirect(url_for('index'))

    form = ProfileCompletionForm()

    # Pre-populate form with existing data
    if request.method == 'GET':
        if current_user.mobile_number != '0000000000':
            form.mobile_number.data = current_user.mobile_number
        if current_user.age != 1:
            form.age.data = current_user.age
        if current_user.sex:
            form.sex.data = current_user.sex

    if form.validate_on_submit():
        try:
            # Update patient profile
            current_user.mobile_number = form.mobile_number.data
            current_user.age = form.age.data
            current_user.sex = form.sex.data

            db.session.commit()
            flash('Profile completed successfully!', 'success')
            return redirect(url_for('patient_dashboard'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating profile: {str(e)}', 'danger')

    return render_template('patient/complete_profile.html', form=form)


@app.route('/patient/edit-profile', methods=['GET', 'POST'])
@login_required
def patient_edit_profile():
    """Patient profile editing route"""
    if not isinstance(current_user, Patient):
        flash('Access denied.', 'danger')
        return redirect(url_for('index'))

    form = PatientEditForm()

    # Pre-populate form with existing data
    if request.method == 'GET':
        form.full_name.data = current_user.full_name
        form.mobile_number.data = current_user.mobile_number
        form.email.data = current_user.email
        form.age.data = current_user.age
        form.sex.data = current_user.sex

    if form.validate_on_submit():
        try:
            # Check if mobile number is being changed and if it already exists
            if form.mobile_number.data != current_user.mobile_number:
                existing_patient = Patient.query.filter(
                    Patient.mobile_number == form.mobile_number.data,
                    Patient.id != current_user.id
                ).first()
                if existing_patient:
                    flash('A patient with this mobile number already exists.', 'danger')
                    return render_template('patient/edit_profile.html', form=form)

            # Check if email is being changed and if it already exists
            if form.email.data and form.email.data != current_user.email:
                existing_patient = Patient.query.filter(
                    Patient.email == form.email.data,
                    Patient.id != current_user.id
                ).first()
                if existing_patient:
                    flash('A patient with this email already exists.', 'danger')
                    return render_template('patient/edit_profile.html', form=form)

            # Update patient profile
            current_user.full_name = form.full_name.data
            current_user.mobile_number = form.mobile_number.data
            current_user.email = form.email.data
            current_user.age = form.age.data
            current_user.sex = form.sex.data

            db.session.commit()
            flash('Profile updated successfully!', 'success')
            return redirect(url_for('patient_dashboard'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating profile: {str(e)}', 'danger')

    return render_template('patient/edit_profile.html', form=form)

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
            appointment.status = 'confirmed'

            # Update payment status to completed when confirmed
            try:
                payment = Payment.query.filter_by(appointment_id=appointment_id).first()
                if payment:
                    payment.status = 'completed'
                    print(f"Updated payment {payment.id} status to completed")  # Debug log
                else:
                    print(f"No payment found for appointment {appointment_id}")  # Debug log

                db.session.commit()

                # Send confirmation email when doctor confirms the appointment
                if appointment.patient.email:
                    subject = "Appointment Confirmed - Dr. Richa's Eye Clinic"
                    message = f"""
Dear {appointment.patient.full_name},

Great news! Your appointment has been CONFIRMED by Dr. Richa.

Confirmed Appointment Details:
- Date: {appointment.appointment_date.strftime('%A, %B %d, %Y')}
- Time: {appointment.appointment_time.strftime('%I:%M %p')}
- Primary Issue: {appointment.primary_issue}
- Consultation Fee: ₹500 (to be paid at the clinic)

Please arrive 15 minutes before your scheduled time.

You will receive a reminder email 7-8 hours before your appointment.

Location: First floor, DVR Town Centre, near to IGUS private limited, 
Mandur, Budigere Road (New Airport Road), Bengaluru, Karnataka 560049

Best regards,
Dr. Richa's Eye Clinic
                    """
                    send_email_notification(appointment.patient.email, subject, message)

                flash('Appointment confirmed and confirmation email sent to patient.', 'success')
                return redirect(url_for('admin_appointment_view', appointment_id=appointment_id))
            except Exception as e:
                db.session.rollback()
                flash(f'Error updating appointment: {str(e)}', 'danger')

        elif action == 'cancel':
            appointment.status = 'cancelled'

            # Update payment status to cancelled as well
            try:
                payment = Payment.query.filter_by(appointment_id=appointment_id).first()
                if payment:
                    payment.status = 'cancelled'
                    print(f"Updated payment {payment.id} status to cancelled")  # Debug log
                else:
                    print(f"No payment found for appointment {appointment_id}")  # Debug log

                db.session.commit()

                # Send cancellation email when doctor cancels the appointment
                if appointment.patient.email:
                    subject = "Appointment Cancelled - Dr. Richa's Eye Clinic"
                    message = f"""
Dear {appointment.patient.full_name},

We regret to inform you that your appointment scheduled for {appointment.appointment_date.strftime('%A, %B %d, %Y')} at {appointment.appointment_time.strftime('%I:%M %p')} has been cancelled by our medical team.

We apologize for any inconvenience caused. Please contact us at your earliest convenience to reschedule your appointment.

You can:
- Call us during clinic hours
- Visit our website to book a new appointment
- Reply to this email with your preferred time slots

We look forward to serving you soon.

Best regards,
Dr. Richa's Eye Clinic
Phone: +91 98765 43210
Location: First floor, DVR Town Centre, near to IGUS private limited, 
Mandur, Budigere Road (New Airport Road), Bengaluru, Karnataka 560049
                    """
                    send_email_notification(appointment.patient.email, subject, message)

                flash('Appointment cancelled and notification sent to patient.', 'warning')
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
    from forms import DoctorPrescriptionForm
    from models import Patient, DoctorPrescription, Doctor
    from datetime import datetime

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

    form = DoctorPrescriptionForm(obj=medical_record)

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

            # Create a comprehensive DoctorPrescription record
            doctor_prescription = DoctorPrescription(
                patient_id=appointment.patient_id,
                doctor_id=doctor.id,
                prescription_date=datetime.utcnow(),
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
                prescribed_eyewear=form.prescribed_eyewear.data,
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
            print(f"Created comprehensive doctor prescription for patient {appointment.patient_id} with doctor {doctor.id}")  # Debug log
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

    # Populate assistant choices
    assistants = Assistant.query.all()
    form.assistant_id.choices = [(assistant.id, f"{assistant.full_name} ({assistant.email})") for assistant in assistants]

    if form.validate_on_submit():
        # Get the selected assistant
        assistant = Assistant.query.get(form.assistant_id.data)
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

                # Send email notification only if assistant has a valid email
                if assistant.email and assistant.email != 'assistant@eyeclinic.com':
                    subject = "Salary Payment Receipt - Dr. Richa's Eye Clinic"
                    message = f"""
Dear {assistant.full_name},

Your salary payment has been processed:

Amount: ₹{form.amount.data}
Date: {form.payment_date.data}
Payment Method: {form.payment_method.data}
Description: {form.description.data}

Best regards,
Dr. Richa's Eye Clinic
"""
                    try:
                        send_email_notification(assistant.email, subject, message)
                        flash('Salary payment processed successfully and notification sent!', 'success')
                    except Exception as email_error:
                        print(f"Email notification failed: {str(email_error)}")
                        flash('Salary payment processed successfully! (Email notification failed)', 'warning')
                else:
                    flash('Salary payment processed successfully! (No email configured for assistant)', 'success')

                return redirect(url_for('admin_assistant_salary'))
            except Exception as e:
                db.session.rollback()
                flash(f'Error processing salary: {str(e)}', 'danger')
                return redirect(url_for('admin_assistant_salary'))
        else:
            flash('No assistant found in the system', 'danger')

    # Get all salary records from all assistants
    assistants = Assistant.query.all()
    salary_records = []
    for assistant in assistants:
        assistant_salaries = Salary.query.filter_by(assistant_id=assistant.id).order_by(desc(Salary.payment_date)).all()
        salary_records.extend(assistant_salaries)

    # Sort all salary records by payment date
    salary_records.sort(key=lambda x: x.payment_date, reverse=True)

    return render_template('admin/assistant_salary.html', form=form, salary_records=salary_records, assistants=assistants)

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

            # Auto-assign date and time slot for walk-in
            today = datetime.now().date()
            current_datetime = datetime.now()
            current_hour = current_datetime.hour
            current_minute = current_datetime.minute

            # Determine if it's Sunday
            is_sunday = today.weekday() == 6

            # Calculate nearest appropriate time slot
            if is_sunday:
                # Sunday: 10 AM to 1 PM slots
                if current_hour < 10:
                    assigned_time = datetime.strptime("10:00", "%H:%M").time()
                elif current_hour >= 13:
                    assigned_time = datetime.strptime("13:00", "%H:%M").time()
                else:
                    # Round to nearest 30-minute slot
                    if current_minute < 30:
                        assigned_time = datetime.strptime(f"{current_hour}:00", "%H:%M").time()
                    else:
                        assigned_time = datetime.strptime(f"{current_hour}:30", "%H:%M").time()
            else:
                # Monday-Saturday: 5 PM to 8 PM slots
                if current_hour < 17:
                    assigned_time = datetime.strptime("17:00", "%H:%M").time()
                elif current_hour >= 20:
                    assigned_time = datetime.strptime("20:00", "%H:%M").time()
                else:
                    # Round to nearest 30-minute slot
                    if current_minute < 30:
                        assigned_time = datetime.strptime(f"{current_hour}:00", "%H:%M").time()
                    else:
                        assigned_time = datetime.strptime(f"{current_hour}:30", "%H:%M").time()

            # Get additional information from form
            referral_info = request.form.get('referral_info', 'Walk-in patient')
            primary_issue = form.primary_issue.data or "Walk-in consultation"

            walk_in_appointment = Appointment(
                patient_id=new_patient.id,
                appointment_date=today,
                appointment_time=assigned_time,
                primary_issue=primary_issue,
                referral_info=referral_info,
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
                notes=f'Walk-in patient added by {current_user.full_name} at {assigned_time.strftime("%I:%M %p")}'
            )
            db.session.add(walk_in_treatment)

            db.session.commit()

            flash(f'Walk-in patient "{new_patient.full_name}" successfully registered for {assigned_time.strftime("%I:%M %p")} and ₹500 consultation fee recorded!', 'success')
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
                prescription_date=datetime.utcnow(),
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
                prescribed_eyewear=form.prescribed_eyewear.data,
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

    # Auto-populate visit date from patient's most recent appointment and branch
    if request.method == 'GET':
        # Get the patient's most recent appointment
        recent_appointment = Appointment.query.filter_by(patient_id=patient_id).order_by(Appointment.appointment_date.desc()).first()

        if recent_appointment:
            form.visit_date.data = recent_appointment.appointment_date
        else:
            form.visit_date.data = datetime.now().date()

        form.branch.data = "Dr. Richa's Eye Clinic - DVR Town Centre, Budigere Road"

    if form.validate_on_submit():
        prescription = OptometristPrescription(
            patient_id=patient_id,
            assistant_id=current_user.id,
            # Primary examination details
            visit_date=form.visit_date.data,
            branch=form.branch.data,
            present_complaints=form.present_complaints.data,
            # Vision assessment
            vision_distance_re=form.vision_distance_re.data,
            vision_distance_le=form.vision_distance_le.data,
            vision_near_re=form.vision_near_re.data,
            vision_near_le=form.vision_near_le.data,
            # Current medication
            current_medication_type=form.current_medication_type.data,
            current_medication_name=form.current_medication_name.data,
            current_medication_dosage=form.current_medication_dosage.data,
            current_medication_eye=form.current_medication_eye.data,
            current_medication_remarks=form.current_medication_remarks.data,
            # Undilated acceptance - Right Eye
            undilated_re_sph=form.undilated_re_sph.data,
            undilated_re_cyl=form.undilated_re_cyl.data,
            undilated_re_axis=form.undilated_re_axis.data,
            undilated_re_prism=form.undilated_re_prism.data,
            undilated_re_va=form.undilated_re_va.data,
            undilated_re_nv=form.undilated_re_nv.data,
            # Undilated acceptance - Left Eye
            undilated_le_sph=form.undilated_le_sph.data,
            undilated_le_cyl=form.undilated_le_cyl.data,
            undilated_le_axis=form.undilated_le_axis.data,
            undilated_le_prism=form.undilated_le_prism.data,
            undilated_le_va=form.undilated_le_va.data,
            undilated_le_nv=form.undilated_le_nv.data,
            # Dilated acceptance - Right Eye
            dilated_re_sph=form.dilated_re_sph.data,
            dilated_re_cyl=form.dilated_re_cyl.data,
            dilated_re_axis=form.dilated_re_axis.data,
            dilated_re_prism=form.dilated_re_prism.data,
            dilated_re_va=form.dilated_re_va.data,
            dilated_re_nv=form.dilated_re_nv.data,
            # Dilated acceptance - Left Eye
            dilated_le_sph=form.dilated_le_sph.data,
            dilated_le_cyl=form.dilated_le_cyl.data,
            dilated_le_axis=form.dilated_le_axis.data,
            dilated_le_prism=form.dilated_le_prism.data,
            dilated_le_va=form.dilated_le_va.data,
            dilated_le_nv=form.dilated_le_nv.data,
            # IOP details
            iop_time=form.iop_time.data,
            iop_method=form.iop_method.data,
            iop_od=form.iop_od.data,
            iop_os=form.iop_os.data,
            iop_dl=form.iop_dl.data,
            iop_pachy=form.iop_pachy.data,
            iop_remarks=form.iop_remarks.data,
            # Final glasses - Right Eye
            final_re_sph=form.final_re_sph.data,
            final_re_cyl=form.final_re_cyl.data,
            final_re_axis=form.final_re_axis.data,
            final_re_prism=form.final_re_prism.data,
            final_re_va=form.final_re_va.data,
            final_re_nv=form.final_re_nv.data,
            # Final glasses - Left Eye
            final_le_sph=form.final_le_sph.data,
            final_le_cyl=form.final_le_cyl.data,
            final_le_axis=form.final_le_axis.data,
            final_le_prism=form.final_le_prism.data,
            final_le_va=form.final_le_va.data,
            final_le_nv=form.final_le_nv.data,
            # Old glasses - Distance
            old_distance_re_sph=form.old_distance_re_sph.data,
            old_distance_re_cyl=form.old_distance_re_cyl.data,
            old_distance_re_axis=form.old_distance_re_axis.data,
            old_distance_re_va=form.old_distance_re_va.data,
            old_distance_le_sph=form.old_distance_le_sph.data,
            old_distance_le_cyl=form.old_distance_le_cyl.data,
            old_distance_le_axis=form.old_distance_le_axis.data,
            old_distance_le_va=form.old_distance_le_va.data,
            # Old glasses - Add
            old_add_re=form.old_add_re.data,
            old_add_le=form.old_add_le.data,
            # Glass type and usage
            type_of_glasses=form.type_of_glasses.data,
            glass_usage=form.glass_usage.data,
            # Lens specifications
            product=form.product.data,
            type_of_lens=form.type_of_lens.data,
            lens_material=form.lens_material.data,
            # Additional fields
            gp_advised_by=form.gp_advised_by.data,
            opto_student=form.opto_student.data,
            keratometer_readings=form.keratometer_readings.data,
            # General remarks and notes
            general_remarks=form.general_remarks.data,
            recommendations=form.recommendations.data,
            notes=form.notes.data
        )
        db.session.add(prescription)
        try:
            db.session.commit()
            flash('Comprehensive optometry prescription added successfully!', 'success')
            return redirect(url_for('assistant_prescriptions'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding prescription: {str(e)}', 'danger')

    return render_template('assistant/add_prescription.html', form=form, patient=patient)

@app.route('/print-prescription/<string:type>/<int:prescription_id>')
def print_prescription(type, prescription_id):
    """Print prescription route"""
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

@app.route('/print-combined-prescription/<int:patient_id>')
def print_combined_prescription(patient_id):
    """Print combined doctor and optometrist prescriptions route"""
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

@app.route('/patient/print-combined-prescription/<int:patient_id>')
@login_required
def patient_print_combined_prescription(patient_id):
    """Patient route to print combined doctor and optometrist prescriptions"""
    # Check if user is authenticated and is a Patient
    if not current_user.is_authenticated:
        flash('Please log in to access your prescriptions.', 'warning')
        return redirect(url_for('patient_login'))

    if not isinstance(current_user, Patient):
        flash('Access denied. Patient privileges required.', 'danger')
        return redirect(url_for('patient_login'))

    # Ensure patient can only access their own prescriptions
    if current_user.id != patient_id:
        flash('Access denied. You can only view your own prescriptions.', 'danger')
        return redirect(url_for('patient_dashboard'))

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
        flash('No prescriptions found.', 'warning')
        return redirect(url_for('patient_medical_records'))

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

@app.route('/patient/google-register')
def patient_google_register():
    """Patient Google OAuth registration route - disabled"""
    flash('Patient registration is no longer available. Please book appointments directly.', 'info')
    return redirect(url_for('appointment'))

    # Check if Google OAuth is configured
    google_client_id = app.config.get('GOOGLE_CLIENT_ID')
    if not google_client_id:
        flash('Google OAuth is not configured. Please contact administrator.', 'danger')
        return redirect(url_for('patient_register'))

    # Generate state for CSRF protection
    state = os.urandom(16).hex()
    session['oauth_state'] = state
    session['oauth_action'] = 'register'

    # Generate redirect URI - use the current host
    if request.host.endswith('.replit.app') or request.host.endswith('.repl.co'):
        google_redirect_uri = f"https://{request.host}/patient/google-callback"
    else:
        google_redirect_uri = url_for('patient_google_callback', _external=True)
        if google_redirect_uri.startswith('http://'):
            google_redirect_uri = google_redirect_uri.replace('http://', 'https://')

    # OAuth parameters
    params = {
        'client_id': google_client_id,
        'redirect_uri': google_redirect_uri,
        'response_type': 'code',
        'scope': 'openid email profile',
        'state': state,
        'access_type': 'online',
        'prompt': 'select_account'
    }

    oauth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"
    print(f"OAuth URL: {oauth_url}")  # Debug log
    print(f"Redirect URI: {google_redirect_uri}")  # Debug log

    # Redirect to Google's OAuth consent screen
    return redirect(oauth_url)

@app.route('/patient/google-login')
def patient_google_login():
    """Patient Google OAuth login route - disabled"""
    flash('Patient login is no longer available. Please book appointments directly.', 'info')
    return redirect(url_for('appointment'))

    # Check if Google OAuth is configured
    google_client_id = app.config.get('GOOGLE_CLIENT_ID')
    if not google_client_id:
        flash('Google OAuth is not configured. Please contact administrator.', 'danger')
        return redirect(url_for('patient_login'))

    # Generate state for CSRF protection
    state = os.urandom(16).hex()
    session['oauth_state'] = state
    session['oauth_action'] = 'login'

    # Generate redirect URI - use the current host
    if request.host.endswith('.replit.app') or request.host.endswith('.repl.co'):
        google_redirect_uri = f"https://{request.host}/patient/google-callback"
    else:
        google_redirect_uri = url_for('patient_google_callback', _external=True)
        if google_redirect_uri.startswith('http://'):
            google_redirect_uri = google_redirect_uri.replace('http://', 'https://')

    # OAuth parameters
    params = {
        'client_id': google_client_id,
        'redirect_uri': google_redirect_uri,
        'response_type': 'code',
        'scope': 'openid email profile',
        'state': state,
        'access_type': 'online',
        'prompt': 'select_account'
    }

    oauth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"
    print(f"OAuth URL: {oauth_url}")  # Debug log
    print(f"Redirect URI: {google_redirect_uri}")  # Debug log

    # Redirect to Google's OAuth consent screen
    return redirect(oauth_url)

@app.route('/patient/google-callback')
def patient_google_callback():
    """Google OAuth callback route"""
    print(f"Google callback received with args: {request.args}")  # Debug log

    # Check for OAuth errors first
    if 'error' in request.args:
        error = request.args.get('error')
        error_description = request.args.get('error_description', '')
        print(f"OAuth error: {error} - {error_description}")  # Debug log
        if error == 'access_denied':
            flash('Google authentication was cancelled.', 'info')
        else:
            flash(f'Google authentication failed: {error}', 'danger')
        return redirect(url_for('patient_register'))

    # Get authorization code
    code = request.args.get('code')
    if not code:
        flash('Authentication failed - no authorization code received.', 'danger')
        return redirect(url_for('patient_register'))

    # State verification
    received_state = request.args.get('state')
    stored_state = session.get('oauth_state')
    if not received_state or received_state != stored_state:
        print(f"State mismatch: received {received_state}, expected {stored_state}")  # Debug log
        flash('Security verification failed. Please try again.', 'danger')
        return redirect(url_for('patient_register'))

    try:
        oauth_action = session.get('oauth_action', 'register')
        google_client_id = app.config.get('GOOGLE_CLIENT_ID')
        google_client_secret = app.config.get('GOOGLE_CLIENT_SECRET')

        if not google_client_id or not google_client_secret:
            flash('Google OAuth configuration error. Please contact administrator.', 'danger')
            return redirect(url_for('patient_register'))

        # Generate redirect URI consistently
        if request.host.endswith('.replit.app') or request.host.endswith('.repl.co'):
            redirect_uri = f"https://{request.host}/patient/google-callback"
        else:
            redirect_uri = url_for('patient_google_callback', _external=True)
            if redirect_uri.startswith('http://'):
                redirect_uri = redirect_uri.replace('http://', 'https://')

        print(f"Token exchange redirect URI: {redirect_uri}")  # Debug log

        # Exchange code for access token
        token_url = "https://oauth2.googleapis.com/token"
        token_data = {
            'code': code,
            'client_id': google_client_id,
            'client_secret': google_client_secret,
            'redirect_uri': redirect_uri,
            'grant_type': 'authorization_code'
        }

        print(f"Making token request to: {token_url}")  # Debug log
        token_response = requests.post(token_url, data=token_data, timeout=30)
        print(f"Token response status: {token_response.status_code}")  # Debug log

        if token_response.status_code != 200:
            print(f"Token response error: {token_response.text}")  # Debug log
            flash('Authentication failed during token exchange.', 'danger')
            return redirect(url_for('patient_register'))

        tokens = token_response.json()
        access_token = tokens.get('access_token')

        if not access_token:
            print(f"No access token in response: {tokens}")  # Debug log
            flash('Authentication failed - no access token received.', 'danger')
            return redirect(url_for('patient_register'))

        print("Access token received successfully")  # Debug log

        # Get user information
        userinfo_response = requests.get(
            "https://www.googleapis.com/oauth2/v3/userinfo",
            headers={'Authorization': f'Bearer {access_token}'},
            timeout=30
        )

        print(f"Userinfo response status: {userinfo_response.status_code}")  # Debug log

        if userinfo_response.status_code != 200:
            print(f"Userinfo response error: {userinfo_response.text}")  # Debug log
            flash('Failed to get user information from Google.', 'danger')
            return redirect(url_for('patient_register'))

        userinfo = userinfo_response.json()
        email = userinfo.get('email')
        name = userinfo.get('name', 'Google User')

        print(f"User info received: email={email}, name={name}")  # Debug log

        if not email:
            flash('Failed to get your email from Google.', 'danger')
            return redirect(url_for('patient_register'))

        # Find or create patient account
        patient = Patient.query.filter_by(email=email).first()

        if not patient:
            if oauth_action == 'login':
                flash('No account found with this Google email. Please register first.', 'warning')
                return redirect(url_for('patient_register'))

            # Create new patient account
            patient = Patient(
                full_name=name,
                email=email,
                mobile_number='0000000000',
                age=1,
                sex='',
                is_registered=True
            )
            db.session.add(patient)
            db.session.commit()
            print(f"Created new patient: {patient.id}")  # Debug log

        # Log in the user
        login_user(patient)
        print(f"Logged in patient: {patient.id}")  # Debug log

        # Clear session data
        session.pop('oauth_state', None)
        session.pop('oauth_action', None)

        # Success message
        if oauth_action == 'register':
            flash('Successfully registered with Google!', 'success')
        else:
            flash('Successfully logged in with Google!', 'success')

        # Redirect to profile completion if needed
        if patient.mobile_number == '0000000000' or patient.age == 1:
            return redirect(url_for('patient_complete_profile'))

        return redirect(url_for('patient_dashboard'))

    except requests.exceptions.RequestException as e:
        print(f"Network error during OAuth: {str(e)}")  # Debug log
        flash('Network error during authentication. Please try again.', 'danger')
        return redirect(url_for('patient_register'))
    except Exception as e:
        print(f"OAuth callback error: {str(e)}")  # Debug log
        flash('An error occurred during authentication. Please try again.', 'danger')
        return redirect(url_for('patient_register'))

@app.route('/admin/fix-payment-status')
@login_required
def admin_fix_payment_status():
    """Debug route to fix inconsistent payment statuses"""
    if not isinstance(current_user, Doctor):
        flash('Access denied. Doctor privileges required.', 'danger')
        return redirect(url_for('index'))

    try:
        fixed_count = 0
        cancelled_count = 0

        # Find payments where appointment is confirmed but payment is still pending
        inconsistent_payments = db.session.query(Payment).join(Appointment).filter(
            Appointment.status == 'confirmed',
            Payment.status == 'pending'
        ).all()

        # Fix them
        for payment in inconsistent_payments:
            payment.status = 'completed'
            fixed_count += 1
            print(f"Fixed payment {payment.id} for appointment {payment.appointment_id}")

        # Find payments where appointment is cancelled but payment is not cancelled
        cancelled_payments = db.session.query(Payment).join(Appointment).filter(
            Appointment.status == 'cancelled',
            Payment.status != 'cancelled'
        ).all()

        for payment in cancelled_payments:
            payment.status = 'cancelled'
            cancelled_count += 1
            print(f"Fixed cancelled payment {payment.id} for appointment {payment.appointment_id}")

        # Also check for payments with completed status where appointment is still scheduled
        completed_payments_wrong = db.session.query(Payment).join(Appointment).filter(
            Appointment.status == 'scheduled',
            Payment.status == 'completed'
        ).all()

        for payment in completed_payments_wrong:
            payment.status = 'pending'
            fixed_count += 1
            print(f"Reset payment {payment.id} for scheduled appointment {payment.appointment_id}")

        db.session.commit()

        flash(f'Fixed {fixed_count} payments and cancelled {cancelled_count} payments', 'success')
        return redirect(url_for('admin_revenue'))

    except Exception as e:
        db.session.rollback()
        flash(f'Error fixing payment statuses: {str(e)}', 'danger')
        return redirect(url_for('admin_revenue'))

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
            patient_name = request.form.get('patient_name')

            # Try to find existing patient by name
            patient = Patient.query.filter_by(full_name=patient_name).first()

            # If patient doesn't exist, create a new one with minimal info
            if not patient:
                patient = Patient(
                    full_name=patient_name,
                    mobile_number='0000000000',  # Default placeholder
                    email='',  # Empty email
                    age=1,  # Default age
                    sex='',  # Empty sex
                    is_registered=False
                )
                db.session.add(patient)
                db.session.flush()  # Get patient ID before commit

            new_treatment = Treatment(
                patient_id=patient.id,
                treatment_name=request.form.get('treatment_name'),
                treatment_date=datetime.strptime(request.form.get('treatment_date'), '%Y-%m-%d').date(),
                amount=float(request.form.get('amount')),
                notes=request.form.get('notes')
            )
            db.session.add(new_treatment)
            db.session.commit()

            if patient.mobile_number == '0000000000':
                flash(f'Treatment record added successfully for new patient: {patient_name}!', 'success')
            else:
                flash('Treatment record added successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding treatment: {str(e)}', 'danger')

    # Get all payments with patient details (exclude cancelled payments and payments from cancelled appointments)
    payments = (
        db.session.query(Payment, Patient)
        .join(Appointment, Payment.appointment_id == Appointment.id)
        .join(Patient, Appointment.patient_id == Patient.id)
        .filter(
            Payment.status != 'cancelled',
            Appointment.status != 'cancelled'
        )
        .order_by(Payment.created_at.desc())
        .all()
    )

    # Get all treatments
    treatments = Treatment.query.order_by(Treatment.treatment_date.desc()).all()

    # Calculate total revenue (exclude cancelled payments)
    appointment_revenue = sum(payment.amount for payment, _ in payments if payment.status == 'completed')
    treatment_revenue = sum(treatment.amount for treatment in treatments)
    total_revenue = appointment_revenue + treatment_revenue

    # Get all patients for the treatment form
    patients = Patient.query.order_by(Patient.full_name).all()

    return render_template('admin/revenue.html', payments=payments, treatments=treatments, patients=patients, total_revenue=total_revenue, form=form)