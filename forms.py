from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, IntegerField, SelectField, DateField, TimeField, PasswordField, HiddenField, SubmitField, FloatField
from wtforms.validators import DataRequired, Length, NumberRange, Optional, Email, EqualTo, ValidationError

class AppointmentForm(FlaskForm):
    full_name = StringField('Full Name', validators=[DataRequired(), Length(min=3, max=100)])
    mobile_number = StringField('Mobile Number', validators=[DataRequired(), Length(min=10, max=15)])
    consultation_fee = IntegerField('Consultation Fee', validators=[Optional()], default=500)
    email = StringField('Email', validators=[Optional(), Email(), Length(max=100)])
    age = IntegerField('Age', validators=[DataRequired(), NumberRange(min=1, max=120)])
    sex = SelectField('Sex', choices=[('', 'Select Sex'), ('male', 'Male'), ('female', 'Female'), ('others', 'Others')], validators=[DataRequired()])
    appointment_date = DateField('Appointment Date', validators=[DataRequired()])
    appointment_time = TimeField('Appointment Time', validators=[DataRequired()])
    primary_issue = TextAreaField('Primary Eye Issue', validators=[Optional(), Length(max=500)])
    referral_info = StringField('Referral Information (if any)', validators=[Optional(), Length(max=255)])
    submit = SubmitField('Book Appointment')

class FindAppointmentForm(FlaskForm):
    mobile_number = StringField('Mobile Number', validators=[Optional(), Length(min=10, max=15)])
    email = StringField('Email Address', validators=[Optional(), Email(), Length(max=100)])
    submit = SubmitField('Find My Appointment')

    def validate(self):
        rv = FlaskForm.validate(self)
        if not rv:
            return False

        # At least one field must be filled
        if not self.mobile_number.data and not self.email.data:
            self.mobile_number.errors.append('Please provide either mobile number or email address')
            self.email.errors.append('Please provide either mobile number or email address')
            return False

        return True

class PaymentForm(FlaskForm):
    payment_method = SelectField('Payment Method', choices=[
        ('upi', 'UPI'),
        ('credit_card', 'Credit Card'),
        ('debit_card', 'Debit Card'),
    ], validators=[DataRequired()])
    submit = SubmitField('Proceed to Payment')

class ReviewForm(FlaskForm):
    patient_name = StringField('Your Name', validators=[DataRequired(), Length(min=3, max=100)])
    rating = SelectField('Rating', choices=[('5', '5 - Excellent'), ('4', '4 - Very Good'), ('3', '3 - Good'), ('2', '2 - Fair'), ('1', '1 - Poor')], validators=[DataRequired()])
    review_text = TextAreaField('Your Review', validators=[DataRequired(), Length(min=10, max=500)])
    submit = SubmitField('Submit Review')

class DoctorLoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=64)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8, max=128)])
    submit = SubmitField('Login')

class AssistantLoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=64)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8, max=128)])
    submit = SubmitField('Login')

class DoctorPrescriptionForm(FlaskForm):
    diagnosis = TextAreaField('Diagnosis', validators=[DataRequired()])
    medications = TextAreaField('Prescribed Medications', validators=[Optional()])
    instructions = TextAreaField('Instructions', validators=[Optional()])
    follow_up = TextAreaField('Follow-up Notes', validators=[Optional()])
    submit = SubmitField('Save Prescription')

class OptometristPrescriptionForm(FlaskForm):
    vision_test = TextAreaField('Vision Test Results', validators=[DataRequired()])
    eye_power = TextAreaField('Eye Power', validators=[Optional()])
    recommendations = TextAreaField('Recommendations', validators=[Optional()])
    notes = TextAreaField('Additional Notes', validators=[Optional()])
    submit = SubmitField('Save Prescription')

class SalaryForm(FlaskForm):
    assistant_id = SelectField('Assistant', coerce=int, validators=[DataRequired()])
    amount = StringField('Salary Amount', validators=[DataRequired()])
    payment_date = DateField('Payment Date', validators=[DataRequired()])
    payment_method = SelectField('Payment Method', choices=[
        ('bank_transfer', 'Bank Transfer'),
        ('cash', 'Cash'),
        ('stripe', 'Stripe'),
        ('other', 'Other')
    ], validators=[DataRequired()])
    description = TextAreaField('Description/Notes', validators=[Optional(), Length(max=500)])
    submit = SubmitField('Process Salary Payment')

# Keep for backward compatibility
class AdminLoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=64)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8, max=128)])
    submit = SubmitField('Login')

class PatientLoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=100)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8, max=128)])
    submit = SubmitField('Login')

class PatientRegistrationForm(FlaskForm):
    full_name = StringField('Full Name', validators=[DataRequired(), Length(min=3, max=100)])
    mobile_number = StringField('Mobile Number', validators=[DataRequired(), Length(min=10, max=15)])
    email = StringField('Email', validators=[Optional(), Length(max=100)])  # Removed Email() validator
    age = IntegerField('Age', validators=[DataRequired(), NumberRange(min=1, max=120)])
    sex = SelectField('Sex', choices=[('', 'Select Sex'), ('male', 'Male'), ('female', 'Female'), ('others', 'Others')], validators=[DataRequired()])
    primary_issue = TextAreaField('Primary Issue', validators=[Optional()])
    password = PasswordField('Password', validators=[Optional(), Length(min=8, max=128)])  # Made optional for walk-ins
    confirm_password = PasswordField('Confirm Password', validators=[Optional(), EqualTo('password')])  # Made optional
    submit = SubmitField('Register')

class OTPVerificationForm(FlaskForm):
    email = HiddenField('Email')
    otp = StringField('OTP Code', validators=[DataRequired(), Length(min=6, max=6)])
    submit = SubmitField('Verify OTP')

class ProfileCompletionForm(FlaskForm):
    mobile_number = StringField('Mobile Number', validators=[DataRequired(), Length(min=10, max=15)])
    age = IntegerField('Age', validators=[DataRequired(), NumberRange(min=1, max=120)])
    sex = SelectField('Sex', choices=[('', 'Select Sex'), ('male', 'Male'), ('female', 'Female'), ('others', 'Others')], validators=[DataRequired()])
    primary_issue = TextAreaField('Primary Eye Concern', validators=[Optional(), Length(max=500)])
    submit = SubmitField('Complete Profile')

class PatientEditForm(FlaskForm):
    full_name = StringField('Full Name', validators=[DataRequired(), Length(min=3, max=100)])
    mobile_number = StringField('Mobile Number', validators=[DataRequired(), Length(min=10, max=15)])
    email = StringField('Email', validators=[Optional(), Email(), Length(max=100)])
    age = IntegerField('Age', validators=[DataRequired(), NumberRange(min=1, max=120)])
    sex = SelectField('Sex', choices=[('', 'Select Sex'), ('male', 'Male'), ('female', 'Female'), ('others', 'Others')], validators=[DataRequired()])
    submit = SubmitField('Update Profile')

class PrescriptionForm(FlaskForm):
    diagnosis = TextAreaField('Diagnosis', validators=[DataRequired()])
    left_eye_findings = TextAreaField('Left Eye Findings', validators=[Optional()])
    right_eye_findings = TextAreaField('Right Eye Findings', validators=[Optional()])
    prescribed_medications = TextAreaField('Prescribed Medications', validators=[Optional()])
    prescribed_eyewear = TextAreaField('Prescribed Eyewear', validators=[Optional()])
    follow_up_instructions = TextAreaField('Follow-up Instructions', validators=[Optional()])
    next_appointment_recommendation = StringField('Next Appointment', validators=[Optional()])
    submit = SubmitField('Save Prescription')

class DoctorPrescriptionForm(FlaskForm):
    # Examination findings
    left_eye_findings = TextAreaField('Left Eye Findings', validators=[Optional()])
    right_eye_findings = TextAreaField('Right Eye Findings', validators=[Optional()])

    # Clinical information
    diagnosis = TextAreaField('Diagnosis', validators=[DataRequired()])
    complaints = TextAreaField('Chief Complaints', validators=[Optional()])
    history = TextAreaField('History', validators=[Optional()])
    examination_notes = TextAreaField('Examination Notes', validators=[Optional()])

    # Investigation and tests
    investigation = TextAreaField('Investigation', validators=[Optional()])
    fall_risk = TextAreaField('Fall Risk Assessment', validators=[Optional()])
    immunization = TextAreaField('Immunization Status', validators=[Optional()])

    # Treatment plan
    medications = TextAreaField('Medications', validators=[DataRequired()])
    prescribed_eyewear = TextAreaField('Prescribed Eyewear', validators=[Optional()])
    prognosis = TextAreaField('Prognosis', validators=[Optional()])
    nutritional_advice = TextAreaField('Nutritional Advice', validators=[Optional()])
    plan_of_care = TextAreaField('Plan of Care', validators=[Optional()])

    # Instructions and follow-up
    instructions = TextAreaField('Instructions', validators=[DataRequired()])
    follow_up = TextAreaField('Follow Up', validators=[Optional()])
    referral_reason = TextAreaField('Referral Reason', validators=[Optional()])
    referred_to_cc = StringField('Referred to CC', validators=[Optional()])

    # Additional notes
    comments = TextAreaField('Comments', validators=[Optional()])
    remarks_for_counselor = TextAreaField('Remarks for Counselor', validators=[Optional()])

    submit = SubmitField('Save Prescription')

class OptometristPrescriptionForm(FlaskForm):
    # Primary Examination Details
    visit_date = DateField('Visit Date', validators=[Optional()])
    branch = StringField('Branch', validators=[Optional()])
    present_complaints = TextAreaField('Present Complaints', validators=[Optional()])

    # Vision Assessment
    vision_distance_re = StringField('Distance Vision RE', validators=[Optional()])
    vision_distance_le = StringField('Distance Vision LE', validators=[Optional()])
    vision_near_re = StringField('Near Vision RE', validators=[Optional()])
    vision_near_le = StringField('Near Vision LE', validators=[Optional()])

    # Current Medication
    current_medication_type = StringField('Medication Type', validators=[Optional()])
    current_medication_name = StringField('Medication Name', validators=[Optional()])
    current_medication_dosage = StringField('Dosage', validators=[Optional()])
    current_medication_eye = SelectField('Eye', choices=[('', 'Select'), ('OD', 'OD'), ('OS', 'OS'), ('OU', 'OU')], validators=[Optional()])
    current_medication_remarks = TextAreaField('Medication Remarks', validators=[Optional()])

    # Undilated Acceptance - Right Eye
    undilated_re_sph = StringField('Sph', validators=[Optional()])
    undilated_re_cyl = StringField('Cyl', validators=[Optional()])
    undilated_re_axis = StringField('Axis', validators=[Optional()])
    undilated_re_prism = StringField('Prism', validators=[Optional()])
    undilated_re_va = StringField('V/A', validators=[Optional()])
    undilated_re_nv = StringField('N.V', validators=[Optional()])

    # Undilated Acceptance - Left Eye
    undilated_le_sph = StringField('Sph', validators=[Optional()])
    undilated_le_cyl = StringField('Cyl', validators=[Optional()])
    undilated_le_axis = StringField('Axis', validators=[Optional()])
    undilated_le_prism = StringField('Prism', validators=[Optional()])
    undilated_le_va = StringField('V/A', validators=[Optional()])
    undilated_le_nv = StringField('N.V', validators=[Optional()])

    # Dilated Acceptance - Right Eye
    dilated_re_sph = StringField('Sph', validators=[Optional()])
    dilated_re_cyl = StringField('Cyl', validators=[Optional()])
    dilated_re_axis = StringField('Axis', validators=[Optional()])
    dilated_re_prism = StringField('Prism', validators=[Optional()])
    dilated_re_va = StringField('V/A', validators=[Optional()])
    dilated_re_nv = StringField('N.V', validators=[Optional()])

    # Dilated Acceptance - Left Eye
    dilated_le_sph = StringField('Sph', validators=[Optional()])
    dilated_le_cyl = StringField('Cyl', validators=[Optional()])
    dilated_le_axis = StringField('Axis', validators=[Optional()])
    dilated_le_prism = StringField('Prism', validators=[Optional()])
    dilated_le_va = StringField('V/A', validators=[Optional()])
    dilated_le_nv = StringField('N.V', validators=[Optional()])

    # IOP Details
    iop_time = StringField('IOP Time', validators=[Optional()])
    iop_method = StringField('Method', validators=[Optional()])
    iop_od = StringField('OD', validators=[Optional()])
    iop_os = StringField('OS', validators=[Optional()])
    iop_dl = StringField('DL', validators=[Optional()])
    iop_pachy = StringField('Pachy', validators=[Optional()])
    iop_remarks = TextAreaField('IOP Remarks', validators=[Optional()])

    # Final Glasses - Right Eye
    final_re_sph = StringField('Sph', validators=[Optional()])
    final_re_cyl = StringField('Cyl', validators=[Optional()])
    final_re_axis = StringField('Axis', validators=[Optional()])
    final_re_prism = StringField('Prism', validators=[Optional()])
    final_re_va = StringField('V/A', validators=[Optional()])
    final_re_nv = StringField('N.V', validators=[Optional()])

    # Final Glasses - Left Eye
    final_le_sph = StringField('Sph', validators=[Optional()])
    final_le_cyl = StringField('Cyl', validators=[Optional()])
    final_le_axis = StringField('Axis', validators=[Optional()])
    final_le_prism = StringField('Prism', validators=[Optional()])
    final_le_va = StringField('V/A', validators=[Optional()])
    final_le_nv = StringField('N.V', validators=[Optional()])

    # Old Glasses - Distance
    old_distance_re_sph = StringField('Sph', validators=[Optional()])
    old_distance_re_cyl = StringField('Cyl', validators=[Optional()])
    old_distance_re_axis = StringField('Axis', validators=[Optional()])
    old_distance_re_va = StringField('V/A', validators=[Optional()])
    old_distance_le_sph = StringField('Sph', validators=[Optional()])
    old_distance_le_cyl = StringField('Cyl', validators=[Optional()])
    old_distance_le_axis = StringField('Axis', validators=[Optional()])
    old_distance_le_va = StringField('V/A', validators=[Optional()])

    # Old Glasses - Add
    old_add_re = StringField('Add RE', validators=[Optional()])
    old_add_le = StringField('Add LE', validators=[Optional()])

    # Glass Type and Usage
    type_of_glasses = StringField('Type of Glasses', validators=[Optional()])
    glass_usage = TextAreaField('Usage of Glasses', validators=[Optional()])

    # Lens Specifications
    product = StringField('Product', validators=[Optional()])
    type_of_lens = StringField('Type of Lens', validators=[Optional()])
    lens_material = StringField('Lens Material', validators=[Optional()])

    # Additional Fields
    gp_advised_by = StringField('GP Advised By', validators=[Optional()])
    opto_student = StringField('Opto/Student', validators=[Optional()])
    keratometer_readings = TextAreaField('Keratometer Readings', validators=[Optional()])

    # General Remarks and Notes
    general_remarks = TextAreaField('General Remarks', validators=[Optional()])
    recommendations = TextAreaField('Recommendations', validators=[Optional()])
    notes = TextAreaField('Additional Notes', validators=[Optional()])

    submit = SubmitField('Save Prescription')