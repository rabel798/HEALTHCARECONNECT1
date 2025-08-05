from datetime import datetime
from app import db
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

class Patient(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    mobile_number = db.Column(db.String(15), nullable=False)
    email = db.Column(db.String(100), nullable=True)
    age = db.Column(db.Integer, nullable=False)
    sex = db.Column(db.String(10), nullable=True)
    password_hash = db.Column(db.String(256), nullable=True)
    is_registered = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    appointments = db.relationship('Appointment', backref='patient', lazy=True)
    doctor_prescriptions = db.relationship('DoctorPrescription', backref='patient', lazy=True)
    optometrist_prescriptions = db.relationship('OptometristPrescription', backref='patient', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        self.is_registered = True

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_id(self):
        return str(self.id)

    def is_active(self):
        return self.is_registered

    def __repr__(self):
        return f'<Patient {self.full_name}>'

class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'), nullable=False)
    appointment_date = db.Column(db.Date, nullable=False)
    appointment_time = db.Column(db.Time, nullable=False)
    primary_issue = db.Column(db.Text, nullable=True)
    referral_info = db.Column(db.String(255), nullable=True)
    status = db.Column(db.String(20), default='scheduled')  # scheduled, completed, cancelled
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    consultation_fee = db.Column(db.Float, nullable=False, default=500.0)
    payment_status = db.Column(db.String(20), default='pending')  # pending, paid

    def __repr__(self):
        return f'<Appointment {self.id} for Patient {self.patient_id}>'

class MedicalRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    appointment_id = db.Column(db.Integer, db.ForeignKey('appointment.id'), nullable=False)
    appointment = db.relationship('Appointment', backref='medical_record', uselist=False)

    # Optometrist Review
    left_eye_assessment = db.Column(db.Text, nullable=True)
    right_eye_assessment = db.Column(db.Text, nullable=True)

    # Doctor Review
    doctor_notes = db.Column(db.Text, nullable=True)
    left_eye_findings = db.Column(db.Text, nullable=True)
    right_eye_findings = db.Column(db.Text, nullable=True)
    additional_remarks = db.Column(db.Text, nullable=True)

    # Prescription and Treatment
    diagnosis = db.Column(db.Text, nullable=True)
    prescribed_medications = db.Column(db.Text, nullable=True)
    prescribed_eyewear = db.Column(db.Text, nullable=True)
    follow_up_instructions = db.Column(db.Text, nullable=True)
    next_appointment_recommendation = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<MedicalRecord {self.id} for Appointment {self.appointment_id}>'

class Payment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    appointment_id = db.Column(db.Integer, db.ForeignKey('appointment.id'), nullable=False)
    appointment = db.relationship('Appointment', backref=db.backref('payment', uselist=False))
    amount = db.Column(db.Float, nullable=False)
    payment_method = db.Column(db.String(50), nullable=False)  # cash, bank_transfer, upi
    transaction_id = db.Column(db.String(100), nullable=True)
    upi_id = db.Column(db.String(100), nullable=True)
    status = db.Column(db.String(20), default='pending')  # pending, completed, failed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Payment {self.id} for Appointment {self.appointment_id}>'

class DoctorPrescription(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctor.id'), nullable=False)
    prescription_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Examination findings
    left_eye_findings = db.Column(db.Text, nullable=True)
    right_eye_findings = db.Column(db.Text, nullable=True)
    
    # Clinical information
    diagnosis = db.Column(db.Text, nullable=True)
    complaints = db.Column(db.Text, nullable=True)
    history = db.Column(db.Text, nullable=True)
    examination_notes = db.Column(db.Text, nullable=True)
    
    # Investigation and tests
    investigation = db.Column(db.Text, nullable=True)
    fall_risk = db.Column(db.Text, nullable=True)
    immunization = db.Column(db.Text, nullable=True)
    
    # Treatment plan
    medications = db.Column(db.Text, nullable=True)
    prescribed_eyewear = db.Column(db.Text, nullable=True)
    prognosis = db.Column(db.Text, nullable=True)
    nutritional_advice = db.Column(db.Text, nullable=True)
    plan_of_care = db.Column(db.Text, nullable=True)
    
    # Instructions and follow-up
    instructions = db.Column(db.Text, nullable=True)
    follow_up = db.Column(db.Text, nullable=True)
    referral_reason = db.Column(db.Text, nullable=True)
    referred_to_cc = db.Column(db.String(200), nullable=True)
    
    # Additional notes
    comments = db.Column(db.Text, nullable=True)
    remarks_for_counselor = db.Column(db.Text, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<DoctorPrescription {self.id} for Patient {self.patient_id}>'

class OptometristPrescription(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'), nullable=False)
    assistant_id = db.Column(db.Integer, db.ForeignKey('assistant.id'), nullable=False)
    prescription_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Primary Examination Details
    visit_date = db.Column(db.Date, nullable=True)
    branch = db.Column(db.String(100), nullable=True)
    present_complaints = db.Column(db.Text, nullable=True)
    
    # Vision Assessment
    vision_distance_re = db.Column(db.String(50), nullable=True)  # Right Eye Distance
    vision_distance_le = db.Column(db.String(50), nullable=True)  # Left Eye Distance
    vision_near_re = db.Column(db.String(50), nullable=True)     # Right Eye Near
    vision_near_le = db.Column(db.String(50), nullable=True)     # Left Eye Near
    
    # Current Medication
    current_medication_type = db.Column(db.String(100), nullable=True)
    current_medication_name = db.Column(db.String(200), nullable=True)
    current_medication_dosage = db.Column(db.String(100), nullable=True)
    current_medication_eye = db.Column(db.String(20), nullable=True)
    current_medication_remarks = db.Column(db.Text, nullable=True)
    
    # Undilated Acceptance - Right Eye
    undilated_re_sph = db.Column(db.String(20), nullable=True)
    undilated_re_cyl = db.Column(db.String(20), nullable=True)
    undilated_re_axis = db.Column(db.String(20), nullable=True)
    undilated_re_prism = db.Column(db.String(20), nullable=True)
    undilated_re_va = db.Column(db.String(20), nullable=True)
    undilated_re_nv = db.Column(db.String(20), nullable=True)
    
    # Undilated Acceptance - Left Eye
    undilated_le_sph = db.Column(db.String(20), nullable=True)
    undilated_le_cyl = db.Column(db.String(20), nullable=True)
    undilated_le_axis = db.Column(db.String(20), nullable=True)
    undilated_le_prism = db.Column(db.String(20), nullable=True)
    undilated_le_va = db.Column(db.String(20), nullable=True)
    undilated_le_nv = db.Column(db.String(20), nullable=True)
    
    # Dilated Acceptance - Right Eye
    dilated_re_sph = db.Column(db.String(20), nullable=True)
    dilated_re_cyl = db.Column(db.String(20), nullable=True)
    dilated_re_axis = db.Column(db.String(20), nullable=True)
    dilated_re_prism = db.Column(db.String(20), nullable=True)
    dilated_re_va = db.Column(db.String(20), nullable=True)
    dilated_re_nv = db.Column(db.String(20), nullable=True)
    
    # Dilated Acceptance - Left Eye
    dilated_le_sph = db.Column(db.String(20), nullable=True)
    dilated_le_cyl = db.Column(db.String(20), nullable=True)
    dilated_le_axis = db.Column(db.String(20), nullable=True)
    dilated_le_prism = db.Column(db.String(20), nullable=True)
    dilated_le_va = db.Column(db.String(20), nullable=True)
    dilated_le_nv = db.Column(db.String(20), nullable=True)
    
    # IOP Details
    iop_time = db.Column(db.String(20), nullable=True)
    iop_method = db.Column(db.String(50), nullable=True)
    iop_od = db.Column(db.String(20), nullable=True)
    iop_os = db.Column(db.String(20), nullable=True)
    iop_dl = db.Column(db.String(20), nullable=True)
    iop_pachy = db.Column(db.String(20), nullable=True)
    iop_remarks = db.Column(db.Text, nullable=True)
    
    # Final Glasses - Right Eye
    final_re_sph = db.Column(db.String(20), nullable=True)
    final_re_cyl = db.Column(db.String(20), nullable=True)
    final_re_axis = db.Column(db.String(20), nullable=True)
    final_re_prism = db.Column(db.String(20), nullable=True)
    final_re_va = db.Column(db.String(20), nullable=True)
    final_re_nv = db.Column(db.String(20), nullable=True)
    
    # Final Glasses - Left Eye
    final_le_sph = db.Column(db.String(20), nullable=True)
    final_le_cyl = db.Column(db.String(20), nullable=True)
    final_le_axis = db.Column(db.String(20), nullable=True)
    final_le_prism = db.Column(db.String(20), nullable=True)
    final_le_va = db.Column(db.String(20), nullable=True)
    final_le_nv = db.Column(db.String(20), nullable=True)
    
    # Old Glasses - Distance
    old_distance_re_sph = db.Column(db.String(20), nullable=True)
    old_distance_re_cyl = db.Column(db.String(20), nullable=True)
    old_distance_re_axis = db.Column(db.String(20), nullable=True)
    old_distance_re_va = db.Column(db.String(20), nullable=True)
    old_distance_le_sph = db.Column(db.String(20), nullable=True)
    old_distance_le_cyl = db.Column(db.String(20), nullable=True)
    old_distance_le_axis = db.Column(db.String(20), nullable=True)
    old_distance_le_va = db.Column(db.String(20), nullable=True)
    
    # Old Glasses - Add
    old_add_re = db.Column(db.String(20), nullable=True)
    old_add_le = db.Column(db.String(20), nullable=True)
    
    # Glass Type and Usage
    type_of_glasses = db.Column(db.String(100), nullable=True)
    glass_usage = db.Column(db.String(100), nullable=True)
    
    # Lens Specifications
    product = db.Column(db.String(200), nullable=True)
    type_of_lens = db.Column(db.String(100), nullable=True)
    lens_material = db.Column(db.String(100), nullable=True)
    
    # Additional Fields
    gp_advised_by = db.Column(db.String(100), nullable=True)
    opto_student = db.Column(db.String(100), nullable=True)
    keratometer_readings = db.Column(db.Text, nullable=True)
    
    # General Remarks and Notes
    general_remarks = db.Column(db.Text, nullable=True)
    recommendations = db.Column(db.Text, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Treatment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'), nullable=False)
    patient = db.relationship('Patient', backref='treatments')
    treatment_name = db.Column(db.String(200), nullable=False)
    treatment_date = db.Column(db.Date, nullable=False)
    amount = db.Column(db.Float, nullable=False)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'), nullable=True)
    patient = db.relationship('Patient', backref='reviews')
    patient_name = db.Column(db.String(100), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    review_text = db.Column(db.Text, nullable=False)
    is_approved = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Review {self.id} by {self.patient_name}>'

# Base class for staff members
class Staff(UserMixin, db.Model):
    __abstract__ = True

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    mobile_number = db.Column(db.String(15), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Doctor(Staff):
    __tablename__ = 'doctor'

    qualifications = db.Column(db.String(200), nullable=True)
    specialization = db.Column(db.String(200), nullable=True)

    def get_id(self):
        # Prefix with 'doctor_' to distinguish from other IDs
        return f'doctor_{self.id}'

    def __repr__(self):
        return f'<Doctor {self.username}>'

class Assistant(Staff):
    __tablename__ = 'assistant'

    position = db.Column(db.String(100), nullable=True, default='Optometrist')
    full_name = db.Column(db.String(100), nullable=True, default='Optometrist')
    joining_date = db.Column(db.Date, nullable=True)

    # Relationship with salary records
    salary_records = db.relationship('Salary', backref='assistant', lazy=True)

    def get_id(self):
        # Prefix with 'assistant_' to distinguish from other IDs
        return f'assistant_{self.id}'

    def __repr__(self):
        return f'<Assistant {self.username}>'

class Salary(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    assistant_id = db.Column(db.Integer, db.ForeignKey('assistant.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    payment_date = db.Column(db.Date, nullable=False)
    payment_method = db.Column(db.String(50), nullable=False)  # bank_transfer, cash, stripe, etc.
    transaction_id = db.Column(db.String(100), nullable=True)
    status = db.Column(db.String(20), default='pending')  # pending, completed, failed
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Salary {self.id} for Assistant {self.assistant_id}>'

# Keeping the Admin model for backward compatibility
class Admin(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_id(self):
        # Prefix with 'admin_' to distinguish from Patient IDs
        return f'admin_{self.id}'

    def __repr__(self):
        return f'<Admin {self.username}>'


class OTP(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), nullable=False, index=True)
    otp_code = db.Column(db.String(6), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)
    is_verified = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f'<OTP for {self.email}>'

    def is_expired(self):
        return datetime.utcnow() > self.expires_at