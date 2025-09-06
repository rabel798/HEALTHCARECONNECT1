import threading
import time
from datetime import datetime, timedelta
from models import Appointment, Patient, db
from flask import current_app
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import logging

def send_email_notification(to_email, subject, message):
    """Send email notification"""
    try:
        # Email configuration
        smtp_server = "smtp.gmail.com"
        smtp_port = 587
        sender_email = os.getenv('SMTP_EMAIL')
        sender_password = os.getenv('SMTP_PASSWORD')

        if not sender_email or not sender_password:
            print("Email credentials not configured")
            return False

        # Create message
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = to_email
        msg['Subject'] = subject

        msg.attach(MIMEText(message, 'html'))

        # Send email
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)

        print(f"Email sent successfully to {to_email}")
        return True

    except Exception as e:
        print(f"Error sending email: {e}")
        return False

def send_beautiful_reminder_email(patient_email, patient_name, appointment_date, appointment_time):
    """Send a beautiful HTML reminder email with clinic logo"""

    # Read and encode the logo image
    logo_path = os.path.join('static', 'img', 'clinic_logo.jpg')
    try:
        with open(logo_path, 'rb') as img_file:
            logo_base64 = base64.b64encode(img_file.read()).decode('utf-8')
    except FileNotFoundError:
        logo_base64 = ""  # Fallback if logo not found

    subject = "🔔 Appointment Reminder - Dr. Richa's Eye Clinic"

    html_message = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Appointment Reminder</title>
        <style>
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                line-height: 1.6;
                margin: 0;
                padding: 0;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            }}
            .container {{
                max-width: 600px;
                margin: 40px auto;
                background: white;
                border-radius: 15px;
                overflow: hidden;
                box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            }}
            .header {{
                background: linear-gradient(135deg, #007bff, #0056b3);
                color: white;
                padding: 30px 20px;
                text-align: center;
            }}
            .logo {{
                max-width: 200px;
                height: auto;
                margin-bottom: 20px;
                border-radius: 10px;
            }}
            .header h1 {{
                margin: 0;
                font-size: 24px;
                font-weight: 300;
            }}
            .header p {{
                margin: 10px 0 0 0;
                font-size: 16px;
                opacity: 0.9;
            }}
            .content {{
                padding: 40px 30px;
            }}
            .greeting {{
                font-size: 18px;
                color: #333;
                margin-bottom: 20px;
            }}
            .reminder-card {{
                background: linear-gradient(135deg, #f8f9fa, #e9ecef);
                border-left: 5px solid #007bff;
                padding: 25px;
                border-radius: 10px;
                margin: 20px 0;
            }}
            .appointment-details {{
                background: white;
                border-radius: 10px;
                padding: 25px;
                margin: 20px 0;
                box-shadow: 0 5px 15px rgba(0,0,0,0.08);
            }}
            .detail-row {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 12px 0;
                border-bottom: 1px solid #eee;
            }}
            .detail-row:last-child {{
                border-bottom: none;
            }}
            .detail-label {{
                font-weight: 600;
                color: #555;
            }}
            .detail-value {{
                color: #333;
                font-weight: 500;
            }}
            .date-time {{
                font-size: 20px;
                color: #007bff;
                font-weight: 700;
            }}
            .instructions {{
                background: #fff3cd;
                border: 1px solid #ffeaa7;
                border-radius: 8px;
                padding: 20px;
                margin: 25px 0;
            }}
            .instructions h4 {{
                color: #856404;
                margin: 0 0 15px 0;
            }}
            .instructions ul {{
                margin: 0;
                padding-left: 20px;
                color: #856404;
            }}
            .instructions li {{
                margin: 8px 0;
            }}
            .footer {{
                background: #f8f9fa;
                padding: 30px;
                text-align: center;
                border-top: 1px solid #dee2e6;
            }}
            .contact-info {{
                margin: 15px 0;
                color: #6c757d;
            }}
            .clinic-address {{
                font-style: italic;
                color: #6c757d;
                line-height: 1.4;
            }}
            .btn {{
                display: inline-block;
                background: linear-gradient(135deg, #28a745, #20c997);
                color: white;
                text-decoration: none;
                padding: 12px 25px;
                border-radius: 25px;
                font-weight: 600;
                margin: 15px 0;
                transition: all 0.3s ease;
            }}
            .reminder-icon {{
                font-size: 40px;
                color: #007bff;
                margin-bottom: 15px;
            }}
            @media (max-width: 600px) {{
                .container {{ margin: 20px; }}
                .content {{ padding: 20px; }}
                .detail-row {{ flex-direction: column; align-items: flex-start; }}
                .detail-value {{ margin-top: 5px; }}
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                {f'<img src="data:image/jpeg;base64,{logo_base64}" alt="Dr. Richa&#39;s Eye Clinic Logo" class="logo">' if logo_base64 else ''}
                <h1>Dr. Richa's Eye Clinic</h1>
                <p>Eyes that Shine, Care that matters</p>
            </div>

            <div class="content">
                <div class="greeting">
                    Dear {patient_name},
                </div>

                <div class="reminder-card">
                    <div style="text-align: center;">
                        <div class="reminder-icon">⏰</div>
                        <h3 style="margin: 0; color: #007bff;">Appointment Reminder</h3>
                        <p style="margin: 10px 0 0 0; color: #666;">Your appointment is scheduled for tomorrow</p>
                    </div>
                </div>

                <div class="appointment-details">
                    <h4 style="text-align: center; color: #007bff; margin-bottom: 20px;">Appointment Details</h4>

                    <div class="detail-row">
                        <span class="detail-label">📅 Date:</span>
                        <span class="detail-value date-time">{appointment_date.strftime('%A, %B %d, %Y')}</span>
                    </div>

                    <div class="detail-row">
                        <span class="detail-label">🕒 Time:</span>
                        <span class="detail-value date-time">{appointment_time.strftime('%I:%M %p')}</span>
                    </div>

                    <div class="detail-row">
                        <span class="detail-label">👩‍⚕️ Doctor:</span>
                        <span class="detail-value">Dr. Richa Sharma</span>
                    </div>

                    <div class="detail-row">
                        <span class="detail-label">💰 Consultation Fee:</span>
                        <span class="detail-value">₹500</span>
                    </div>
                </div>

                <div class="instructions">
                    <h4>📋 Important Instructions:</h4>
                    <ul>
                        <li><strong>Arrive 15 minutes early</strong> for check-in and registration</li>
                        <li><strong>Bring your previous prescriptions</strong> and any existing eyewear</li>
                        <li><strong>Carry a valid ID proof</strong> for verification</li>
                        <li><strong>Payment:</strong> Cash, UPI, or Card accepted at the clinic</li>
                        <li><strong>Bring current medications list</strong> if you're taking any eye drops</li>
                    </ul>
                </div>

                <div style="text-align: center; margin: 30px 0;">
                    <p style="color: #666; margin-bottom: 15px;">Need to reschedule or have questions?</p>
                    <a href="mailto:drrichaeyeclinic@gmail.com" class="btn">Contact Us</a>
                </div>

                <div style="background: #e3f2fd; padding: 20px; border-radius: 10px; text-align: center;">
                    <h4 style="color: #1976d2; margin: 0 0 10px 0;">📍 Clinic Location</h4>
                    <div class="clinic-address">
                        First floor, DVR Town Centre<br>
                        Near to IGUS Private Limited<br>
                        Mandur, Budigere Road (New Airport Road)<br>
                        Bengaluru, Karnataka 560049
                    </div>
                </div>
            </div>

            <div class="footer">
                <div class="contact-info">
                    📧 Email: drrichaeyeclinic@gmail.com<br>
                    📱 Phone: +91 98765 43210<br>
                    🌐 Website: Visit our clinic portal
                </div>
                <p style="color: #adb5bd; font-size: 12px; margin: 20px 0 0 0;">
                    This is an automated reminder. Please do not reply to this email.
                </p>
            </div>
        </div>
    </body>
    </html>
    """

    return send_email_notification(patient_email, subject, html_message)

def check_and_send_reminders():
    """Check for appointments that need reminder emails"""
    try:
        from app import app
        with app.app_context():
            # Calculate the target time (7-8 hours before appointment)
            now = datetime.now()
            target_start = now + timedelta(hours=7)
            target_end = now + timedelta(hours=8)

            print(f"Checking for appointments between {target_start} and {target_end}")

            # Find confirmed appointments that need reminders
            appointments_needing_reminders = Appointment.query.filter(
                Appointment.status == 'confirmed',
                Appointment.appointment_date == target_start.date(),
                Appointment.appointment_time >= target_start.time(),
                Appointment.appointment_time <= target_end.time()
            ).all()

            print(f"Found {len(appointments_needing_reminders)} appointments needing reminders")nders)} appointments needing reminders")

            for appointment in appointments_needing_reminders:
                if appointment.patient.email:
                    print(f"Sending reminder to {appointment.patient.email} for appointment on {appointment.appointment_date} at {appointment.appointment_time}")
                    send_beautiful_reminder_email(
                        appointment.patient.email,
                        appointment.patient.full_name,
                        appointment.appointment_date,
                        appointment.appointment_time
                    )
                else:
                    print(f"No email found for patient {appointment.patient.full_name}")

        except Exception as e:
            print(f"Error in reminder check: {str(e)}")

def start_reminder_service():
    """Start the reminder service that checks every hour"""
    def reminder_loop():
        while True:
            try:
                check_and_send_reminders()
                # Sleep for 1 hour (3600 seconds)
                time.sleep(3600)
            except Exception as e:
                print(f"Error in reminder service: {str(e)}")
                time.sleep(300)  # Wait 5 minutes before retrying

    # Start the reminder service in a separate thread
    reminder_thread = threading.Thread(target=reminder_loop, daemon=True)
    reminder_thread.start()
    print("Reminder service started successfully")

# Manual trigger function for testing
def send_test_reminder(appointment_id):
    """Send a test reminder for a specific appointment"""
    try:
        from app import app
        with app.app_context():
            appointment = Appointment.query.get(appointment_id)
            if appointment and appointment.patient.email:
                return send_beautiful_reminder_email(
                    appointment.patient.email,
                    appointment.patient.full_name,
                    appointment.appointment_date,
                    appointment.appointment_time
                )
    except Exception as e:
        print(f"Error sending test reminder: {str(e)}")
        return False_time
            )
        return False