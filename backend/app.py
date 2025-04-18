import datetime
from flask import Flask, redirect, request, jsonify, send_from_directory, session
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity, unset_jwt_cookies
import os, base64, hashlib, json
from flask_cors import CORS
import requests
from sqlalchemy.exc import SQLAlchemyError
from dotenv import load_dotenv
from werkzeug.utils import secure_filename
from flask_restx import Api
from flask_restx import Namespace
import secrets
import smtplib
from email.message import EmailMessage

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
CORS(app)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("postgres-setup-url") # Replace <user>, <password>, <database_name>
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY') # DONT FORGET ABOUT THE .env file that's gitignored
api = Api(app, version='1.0', title='Health API', description='A simple Health API')
# Allowed file extensions
ALLOWED_EXTENSIONS = {'pdf', 'docx'}
UPLOAD_FOLDER = 'uploads'
TOKEN_FILE_PATH = 'fitbit_token.json'
USER = ''
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

gmail_user = "superhear.csc301@gmail.com"
gmail_pass = os.getenv("gmail_pass")

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
jwt = JWTManager(app)

# MODELS
class Patient(db.Model):
    __tablename__ = 'patient'

    u_id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.Text, nullable=False, unique=True)
    name = db.Column(db.Text, nullable=False)
    password = db.Column(db.Text, nullable=False)
    phone_number = db.Column(db.String(15), nullable=False, unique=False, default="000-000-0000")  # Default phone number
    avg_heartrate = db.Column(db.Integer, default=70)
    heart_score = db.Column(db.Integer, default=0)
    steps = db.Column(db.Integer, default=0) # NOTE: this is the latest step field now
    breathing_rate = db.Column(db.Integer, default=16)
    spo2 = db.Column(db.Float, default=98.0)
    ecg = db.Column(db.Text, default="Normal")
    sleep = db.Column(db.Float, default=7.0)



class Doctor(db.Model):
    __tablename__ = 'doctor'

    u_id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.Text, nullable=False, unique=True)
    name = db.Column(db.Text, nullable=False)
    password = db.Column(db.Text, nullable=False)
    specialty = db.Column(db.Text)

class Friendship(db.Model):
    __tablename__ = 'friendship'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    friend_id = db.Column(db.Integer, nullable=False)
    user_type = db.Column(db.String(10), nullable=False)  # 'patient' or 'doctor'
    friend_type = db.Column(db.String(10), nullable=False)  # 'patient' or 'doctor'
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

    # Define relationships
    user_patient = db.relationship('Patient', foreign_keys=[user_id],
                                 primaryjoin="and_(Friendship.user_id==Patient.u_id, "
                                           "Friendship.user_type=='patient')")
    user_doctor = db.relationship('Doctor', foreign_keys=[user_id],
                                primaryjoin="and_(Friendship.user_id==Doctor.u_id, "
                                          "Friendship.user_type=='doctor')")
    friend_patient = db.relationship('Patient', foreign_keys=[friend_id],
                                   primaryjoin="and_(Friendship.friend_id==Patient.u_id, "
                                             "Friendship.friend_type=='patient')")
    friend_doctor = db.relationship('Doctor', foreign_keys=[friend_id],
                                  primaryjoin="and_(Friendship.friend_id==Doctor.u_id, "
                                            "Friendship.friend_type=='doctor')")

class FriendRequest(db.Model):
    __tablename__ = 'friend_request'

    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, nullable=False)
    receiver_id = db.Column(db.Integer, nullable=False)
    sender_type = db.Column(db.String(10), nullable=False)  # 'patient' or 'doctor'
    receiver_type = db.Column(db.String(10), nullable=False)  # 'patient' or 'doctor'
    status = db.Column(db.String(10), default='pending')  # 'pending', 'accepted', 'rejected'
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

    # Define relationships
    sender_patient = db.relationship('Patient', foreign_keys=[sender_id],
                                primaryjoin="and_(FriendRequest.sender_id==Patient.u_id, "
                                          "FriendRequest.sender_type=='patient')")
    sender_doctor = db.relationship('Doctor', foreign_keys=[sender_id],
                                primaryjoin="and_(FriendRequest.sender_id==Doctor.u_id, "
                                          "FriendRequest.sender_type=='doctor')")
    receiver_patient = db.relationship('Patient', foreign_keys=[receiver_id],
                                   primaryjoin="and_(FriendRequest.receiver_id==Patient.u_id, "
                                             "FriendRequest.receiver_type=='patient')")
    receiver_doctor = db.relationship('Doctor', foreign_keys=[receiver_id],
                                  primaryjoin="and_(FriendRequest.receiver_id==Doctor.u_id, "
                                            "FriendRequest.receiver_type=='doctor')")

# UPDATED ROUTES
@app.route('/register/<type>', methods=['POST'])
def register(type):
    if type not in ['patient', 'doctor']:
        return jsonify({"error": "Invalid registration type"}), 400

    data = request.get_json()

    # Validate required fields
    if not all(key in data for key in ['email', 'name', 'password']):
        return jsonify({"error": "Missing required fields"}), 400

    # Check if email already exists in either doctors or patients
    if Doctor.query.filter_by(email=data['email']).first() or \
       Patient.query.filter_by(email=data['email']).first():
        return jsonify({"error": "Email already registered"}), 409

    try:
        # Hash the password
        hashed_password = bcrypt.generate_password_hash(data['password']).decode('utf-8')

        if type == 'doctor':
            new_user = Doctor(
                email=data['email'],
                name=data['name'],
                password=hashed_password,
                specialty=data.get('specialty', '')
            )
        else:  # patient
            new_user = Patient(
                email=data['email'],
                name=data['name'],
                password=hashed_password,
                heart_score=0,
                steps=0
            )
        print(new_user)
        welcome_user(new_user.email, new_user.name)

        db.session.add(new_user)
        db.session.commit()

        return jsonify({"message": f"{type.capitalize()} registration successful"}), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Registration failed: {str(e)}"}), 500

# Update your login route to check both tables
@app.route('/login', methods=['POST'])
def login():
    # with open(TOKEN_FILE_PATH, "w") as file:
    #     json.dump({}, file)
    data = request.get_json()
    # print(data)
    if not data.get('email') or not data.get('password'):
        return jsonify({"error": "Email and password are required"}), 400

    # Check both doctors and patients
    user = Doctor.query.filter_by(email=data['email']).first() or \
           Patient.query.filter_by(email=data['email']).first()

    print(Patient, Doctor, user)
    if not user:
        return jsonify({"error": "User not found"}), 404

    if not bcrypt.check_password_hash(user.password, data['password']):
        return jsonify({"error": "Invalid password"}), 401

    # Create token with user type information
    user_type = 'doctor' if isinstance(user, Doctor) else 'patient'
    access_token = create_access_token(identity=user.email)

    # Check if this is a first login (heart_score will be 0 for new patients)
    is_first_login = isinstance(user, Patient) and user.heart_score == 0

    return jsonify({
        "message": "Login successful",
        "access_token": access_token,
        "user_type": user_type,
        "u_id": user.u_id,
        "is_first_login": is_first_login
    }), 200

# JWT-Protected Route
# Example of a protected route
# Uncomment this and use when trying out protected routes
@app.route('/protected', methods=['GET'])
@jwt_required()
def protected():
    current_user_id = get_jwt_identity()
    user = Patient.query.get(current_user_id)

    return jsonify({"message": "Access granted", "user": {"u_id": user.u_id, "name": user.name}}), 200

password_reset_tokens = {}  # Store email -> token mapping

@app.route('/request_password_reset', methods=['POST'])
def request_password_reset():
    data = request.get_json()
    email = data.get('email')
    
    # Check if email exists in the system
    user = Patient.query.filter_by(email=email).first() or Doctor.query.filter_by(email=email).first()
    
    if not user:
        return jsonify({'message': 'If this email exists in our system, a reset link has been sent'}), 200
    
    # Generate a reset token
    reset_token = secrets.token_hex(16)
    password_reset_tokens[email] = reset_token
    
    # Print token to console for development purposes
    print(f"PASSWORD RESET TOKEN for {email}: {reset_token}")
    # Send email using Gmail
    try:
        gmail_user = "superhear.csc301@gmail.com"
        gmail_pass = os.getenv("gmail_pass")

        msg = EmailMessage()
        msg["From"] = gmail_user
        msg["To"] = email
        msg["Subject"] = "Super Heart Password Reset"

        html_content = f"""
        <html>
        <head>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.5;
                    color: #333;
                }}
                h1 {{
                    color: #d22;
                }}
                .code {{
                    background-color: #f5f5f5;
                    padding: 10px 15px;
                    border-radius: 4px;
                    font-family: monospace;
                    font-size: 16px;
                    border-left: 4px solid #d22;
                    margin: 15px 0;
                }}
                .note {{
                    font-size: 14px;
                    color: #666;
                    margin-top: 20px;
                }}
            </style>
        </head>
        <body>
            <h1>Password Reset Request</h1>
            <p>We received a request to reset your password for your Super Heart account.</p>
            <p>Your password reset code is:</p>
            <div class="code">{reset_token}</div>
            <p>Enter this code along with your new password on the password reset page.</p>
            <p>If you didn't request a password reset, please ignore this email or contact support.</p>
            <p class="note">This code will expire after use.</p>
            <p><strong>Best regards,</strong><br>The Super Heart Team</p>
        </body>
        </html>
        """

        msg.set_content("Your password reset code is: " + reset_token)
        msg.add_alternative(html_content, subtype="html")

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(gmail_user, gmail_pass)
            server.send_message(msg)
        print("Password reset email sent successfully!")
        
    except Exception as e:
        print(f"Error sending password reset email: {e}")
        # Continue anyway so the API call succeeds
    
    return jsonify({'message': 'If this email exists in our system, a reset link has been sent'}), 200

@app.route('/reset_password', methods=['POST'])
def reset_password():
    data = request.get_json()
    email = data.get('email')
    reset_token = data.get('reset_token')
    new_password = data.get('new_password')
    
    # Validate token
    if email not in password_reset_tokens or password_reset_tokens[email] != reset_token:
        return jsonify({'message': 'Invalid or expired reset token'}), 400
    
    # Update password
    user = Patient.query.filter_by(email=email).first() or Doctor.query.filter_by(email=email).first()
    
    if user:
        # Hash the password
        hashed_password = bcrypt.generate_password_hash(new_password).decode('utf-8')
        user.password = hashed_password
        db.session.commit()
    
    # Remove used token
    del password_reset_tokens[email]

    return jsonify({'message': 'Password reset successful'}), 200
# @jwt_required()
# def protected():
#     current_user = get_jwt_identity()

#     # Handle the case where identity is a dict
#     if isinstance(current_user, dict):
#         user_type = current_user.get('type')
#         user_email = current_user.get('email')

#         if user_
# type == 'doctor':
#             user = Doctor.query.filter_by(email=user_email).first()
#         else:
#             user = Patient.query.filter_by(email=user_email).first()
#     else:
#         # Fallback for old tokens
#         user = Patient.query.filter_by(email=current_user).first() or \
#                Doctor.query.filter_by(email=current_user).first()

#     if not user:
#         return jsonify({"error": "User not found"}), 404

#     return jsonify({
#         "message": "Access granted",
#         "user": {
#             "u_id": user.u_id,
#             "name": user.name,
#             "type": "doctor" if isinstance(user, Doctor) else "patient"
#         }
#     }), 200

@app.route('/create_patient', methods=['POST'])
# Uncomment the next line if you want to protect this route with JWT authentication
# @jwt_required()
def create_patient():
    data = request.get_json()

    # Check if data is provided
    if not data:
        return jsonify({"error": "No data provided"}), 400

    # Validate required fields
    if 'email' not in data or 'password' not in data:
        return jsonify({"error": "Missing required fields: email and password"}), 400

    # Check if a patient with this email already exists
    if Patient.query.filter_by(email=data['email']).first():
        return jsonify({"error": "Email already registered"}), 400

    # Hash the password
    hashed_password = bcrypt.generate_password_hash(data['password']).decode('utf-8')

    # Create a new Patient object
    new_patient = Patient(
        name=data.get('name', data['email']),
        email=data['email'],
        password=hashed_password,
        avg_heartrate=data.get('avg_heartrate', 0),
        heart_score=data.get('heart_score', 0),
        steps=data.get('steps', 0)
    )

    try:
        db.session.add(new_patient)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Error creating patient", "details": str(e)}), 500

    return jsonify({"message": "Patient created successfully", "u_id": new_patient.u_id}), 201

# Doctor Editing 
@app.route('/edit_doctor', methods=['POST'])
# Uncomment the next line if you want to protect this route with JWT authentication
@jwt_required()
def edit_doctor():
    data = request.get_json()

    current_user_email = get_jwt_identity()
    doctor = Doctor.query.filter_by(email=current_user_email).first()
    if not doctor:
        return jsonify({"error": "Doctor not found"}), 404
    
    missing_keys = set(doctor.__dict__.keys()) - set(data.keys())
    if missing_keys:
        return jsonify({"error": "NON-EXISTENT FIELD IN REQUEST"}), 400

    if 'name' in data:
        doctor.name = data['name']
    if 'email' in data:
        doctor.email = data['email']
    if 'password' in data:
        hashed_password = bcrypt.generate_password_hash(data['password']).decode('utf-8')
        doctor.password = hashed_password
    if 'specialty' in data:
        doctor.specialty = data['specialty']

    try:
        db.session.commit()
        
        notify_user(doctor.email, doctor.name)

        return jsonify({"message": "Doctor updated successfully"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


# Patient Editing 
@app.route('/edit_patient', methods=['POST'])
# Uncomment the next line if you want to protect this route with JWT authentication
@jwt_required()
def edit_patient():
    data = request.get_json()

    current_user_email = get_jwt_identity()
    patient = Patient.query.filter_by(email=current_user_email).first()

    missing_keys = set(patient.__dict__.keys()) - set(data.keys())
    if missing_keys:
        return jsonify({"error": "NON-EXISTENT FIELD IN REQUEST"}), 400

    if not patient:
        return jsonify({"error": "Patient not found"}), 404

    if 'name' in data:
        patient.name = data['name']
    if 'email' in data:
        patient.email = data['email']
    if 'password' in data:
        hashed_password = bcrypt.generate_password_hash(data['password']).decode('utf-8')
        patient.password = hashed_password
    if 'avg_heartrate' in data:
        patient.avg_heartrate = data['avg_heartrate']
    if 'heart_score' in data:
        patient.heart_score = data['heart_score']
    if 'steps' in data:
        patient.steps = data['steps']

    try:
        db.session.commit()

        notify_user(patient.email, patient.name)

        return jsonify({"message": "Patient updated successfully"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


# Patient Deletion
@app.route('/remove_patient/<int:u_id>', methods=['DELETE'])
@jwt_required()
def remove_patient(u_id):
    patient = Patient.query.get(u_id)
    if not patient:
        return jsonify({"error": "Patient not found"}), 404

    Friendship.query.filter(
        (Friendship.patient_id == u_id) | (Friendship.friend_id == u_id)
    ).delete()

    db.session.delete(patient)
    db.session.commit()

    return jsonify({"message": "Patient and related friendships removed successfully"}), 200
@app.route('/get_weekly_steps', methods=['GET'])
@jwt_required()
def get_weekly_steps():
    user_email = get_jwt_identity()
    patient = Patient.query.filter_by(email=user_email).first()
    with open(TOKEN_FILE_PATH, 'r') as file:
        tokens = json.load(file)
    try: 
        if tokens['user'] and tokens['user'] != user_email:
            return jsonify({"error": "Unauthorized"}), 401  
    except:
        pass
    if not patient:
        return jsonify({"error": "Patient not found"}), 404
    try:
        # Get Fitbit data for the last 7 days
        end_date = datetime.date.today()
        start_date = end_date - datetime.timedelta(days=6)
        
        # Fetch the access token
        access_token, _ = load_tokens_from_file()
        if not access_token:
            return jsonify({"error": "Fitbit not connected"}), 400
        # Fetch step data from Fitbit API
        url = f"https://api.fitbit.com/1/user/-/activities/steps/date/{start_date}/{end_date}.json"
        response = requests.get(url, headers={
            'Authorization': f'Bearer {access_token}',
            'Accept': 'application/json'
        })
        # Handle token expiration
        if response.status_code == 401:
            # Refresh the token and retry
            client_id = os.getenv("CLIENT_ID")
            client_secret = os.getenv("CLIENT_SECRET")
            _, refresh_token = load_tokens_from_file()
            access_token, _ = refresh_fitbit_tokens(client_id, client_secret, refresh_token)
            
            if not access_token:
                return jsonify({"error": "Failed to refresh Fitbit token"}), 500

            # Retry the request with the new token
            response = requests.get(url, headers={
                'Authorization': f'Bearer {access_token}',
                'Accept': 'application/json'
            })

        if response.status_code != 200:
            return jsonify({"error": "Failed to fetch Fitbit data"}), 500
        # Process the response
        fitbit_data = response.json().get('activities-steps', [])
        steps_dict = {entry['dateTime']: int(entry['value']) for entry in fitbit_data}
        # Fill in missing days with 0 steps
        complete_data = []
        for i in range(7):
            date = (end_date - datetime.timedelta(days=6-i)).strftime('%Y-%m-%d')
            complete_data.append({
                "date": date,
                "steps": steps_dict.get(date, 0)
            })
        return jsonify({"weekly_steps": complete_data}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Uncomment and update these routes in app.py
@app.route('/get_weekly_heart_rate', methods=['GET'])
@jwt_required()
def get_weekly_heart_rate():
    user_email = get_jwt_identity()
    patient = Patient.query.filter_by(email=user_email).first()
    
    with open(TOKEN_FILE_PATH, 'r') as file:
        tokens = json.load(file)
    
    try: 
        if tokens['user'] and tokens['user'] != user_email:
            return jsonify({"error": "Unauthorized"}), 401  
    except:
        pass
    
    if not patient:
        return jsonify({"error": "Patient not found"}), 404

    try:
        end_date = datetime.date.today()
        start_date = end_date - datetime.timedelta(days=6)
        
        access_token, _ = load_tokens_from_file()
        if not access_token:
            return jsonify({"error": "Fitbit not connected"}), 400

        url = f"https://api.fitbit.com/1/user/-/activities/heart/date/{start_date}/{end_date}.json"
        response = requests.get(url, headers={
            'Authorization': f'Bearer {access_token}',
            'Accept': 'application/json'
        })

        if response.status_code == 401:
            client_id = os.getenv("CLIENT_ID")
            client_secret = os.getenv("CLIENT_SECRET")
            _, refresh_token = load_tokens_from_file()
            access_token, _ = refresh_fitbit_tokens(client_id, client_secret, refresh_token)
            
            if not access_token:
                return jsonify({"error": "Failed to refresh Fitbit token"}), 500

            response = requests.get(url, headers={
                'Authorization': f'Bearer {access_token}',
                'Accept': 'application/json'
            })

        if response.status_code != 200:
            return jsonify({"error": "Failed to fetch Fitbit data"}), 500

        fitbit_data = response.json().get('activities-heart', [])
        heart_rate_dict = {}
        for entry in fitbit_data:
            date = entry['dateTime']
            heart_rate_dict[date] = entry['value'].get('restingHeartRate', patient.avg_heartrate)

        complete_data = []
        for i in range(7):
            date = (end_date - datetime.timedelta(days=6-i)).strftime('%Y-%m-%d')
            complete_data.append({
                "date": date,
                "heart_rate": heart_rate_dict.get(date, patient.avg_heartrate)
            })

        return jsonify({"weekly_heart_rate": complete_data}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# @app.route('/get_weekly_spo2', methods=['GET'])
# @jwt_required()
# def get_weekly_spo2():
#     user_email = get_jwt_identity()
#     patient = Patient.query.filter_by(email=user_email).first()
    
#     if not patient:
#         return jsonify({"error": "Patient not found"}), 404

#     try:
#         end_date = datetime.date.today()
#         start_date = end_date - datetime.timedelta(days=6)
        
#         access_token, _ = load_tokens_from_file()
#         if not access_token:
#             return jsonify({"error": "Fitbit not connected"}), 400

#         url = f"https://api.fitbit.com/1/user/-/spo2/date/{start_date}/{end_date}.json"
#         response = requests.get(url, headers={
#             'Authorization': f'Bearer {access_token}',
#             'Accept': 'application/json'
#         })

#         if response.status_code == 401:
#             client_id = os.getenv("CLIENT_ID")
#             client_secret = os.getenv("CLIENT_SECRET")
#             _, refresh_token = load_tokens_from_file()
#             access_token, _ = refresh_fitbit_tokens(client_id, client_secret, refresh_token)
            
#             if not access_token:
#                 return jsonify({"error": "Failed to refresh Fitbit token"}), 500

#             response = requests.get(url, headers={
#                 'Authorization': f'Bearer {access_token}',
#                 'Accept': 'application/json'
#             })

#         if response.status_code != 200:
#             return jsonify({"error": "Failed to fetch Fitbit data"}), 500

#         fitbit_data = response.json().get('spo2', [])
#         spo2_dict = {}
        
#         # Handle Fitbit's different response structure
#         for entry in fitbit_data:
#             date = entry['dateTime']
#             # Check for both possible response formats
#             if 'minutes' in entry['value']:
#                 # Daily average format
#                 spo2_dict[date] = entry['value'].get('avg', patient.spo2 or 98.0)
#             else:
#                 # Direct value format
#                 spo2_dict[date] = entry['value'].get('avg', patient.spo2 or 98.0)
        
#         complete_data = []
#         for i in range(7):
#             date = (end_date - datetime.timedelta(days=6-i)).strftime('%Y-%m-%d')
#             complete_data.append({
#                 "date": date,
#                 "spo2": spo2_dict.get(date, patient.spo2)
#             })

#         return jsonify({"weekly_spo2": complete_data}), 200

#     except Exception as e:
#         return jsonify({"error": str(e)}), 500
    

############################################################################################################################
# FRIEND ROUTES
@app.route('/add_friend', methods=['POST'])
@jwt_required()
def add_friend():
    try:
        current_user = get_jwt_identity()
        user_type = get_user_type_from_email(current_user)
        
        # Get data from request body
        data = request.get_json()
        print(f"Received add_friend request with data: {data}")  # Add this debug line
        
        friend_id = data.get('friend_id')
        friend_type = data.get('friend_type')
        
        if not friend_id or not friend_type:
            print(f"Missing data: friend_id={friend_id}, friend_type={friend_type}")
            return jsonify({'error': 'Missing friend_id or friend_type'}), 400
        
        # Get current user ID
        if user_type == 'patient':
            user = Patient.query.filter_by(email=current_user).first()
        else:
            user = Doctor.query.filter_by(email=current_user).first()
        
        if not user:
            print(f"User not found: {current_user}")
            return jsonify({'error': 'User not found'}), 404
        
        # Check if a request already exists
        existing_request = FriendRequest.query.filter(
            ((FriendRequest.sender_id == user.u_id) & (FriendRequest.sender_type == user_type) &
             (FriendRequest.receiver_id == friend_id) & (FriendRequest.receiver_type == friend_type)) |
            ((FriendRequest.sender_id == friend_id) & (FriendRequest.sender_type == friend_type) &
             (FriendRequest.receiver_id == user.u_id) & (FriendRequest.receiver_type == user_type))
        ).first()
        
        if existing_request:
            print(f"Friend request already exists: {existing_request.id}")
            return jsonify({'error': 'Friend request already exists', 'status': 'existing_request'}), 400
        
        # Check if already friends
        existing_friendship = Friendship.query.filter(
            ((Friendship.user_id == user.u_id) & (Friendship.user_type == user_type) &
             (Friendship.friend_id == friend_id) & (Friendship.friend_type == friend_type)) |
            ((Friendship.user_id == friend_id) & (Friendship.user_type == friend_type) &
             (Friendship.friend_id == user.u_id) & (Friendship.friend_type == user_type))
        ).first()
        
        if existing_friendship:
            print(f"Already friends: {existing_friendship.id}")
            return jsonify({'error': 'You are already friends', 'status': 'already_friends'}), 400
        
        # Create and save the friend request
        friend_request = FriendRequest(
            sender_id=user.u_id,
            sender_type=user_type,
            receiver_id=friend_id,
            receiver_type=friend_type,
            status='pending'
        )
        
        db.session.add(friend_request)
        db.session.commit()
        print(f"Friend request created successfully: {friend_request.id}")
        
        return jsonify({'message': 'Friend request sent successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        print(f"Error in add_friend: {str(e)}")
        return jsonify({'error': str(e)}), 500

# Friend List
@app.route('/list_friends', methods=['GET'])
@jwt_required()
def list_friends():
    try:
        user_email = get_jwt_identity()
        
        # Check if user is patient or doctor
        patient = Patient.query.filter_by(email=user_email).first()
        if patient:
            # Get patient's friends (both patients and doctors)
            patient_friends = Friendship.query.filter_by(
                user_id=patient.u_id,
                user_type='patient'
            ).all()
            
            friends_list = []
            for friendship in patient_friends:
                friend_data = {}
                if friendship.friend_type == 'patient':
                    friend = Patient.query.get(friendship.friend_id)
                    friend_data = {
                        "u_id": friend.u_id,
                        "name": friend.name,
                        "type": "patient",
                        "heart_score": friend.heart_score
                    }
                else:
                    friend = Doctor.query.get(friendship.friend_id)
                    friend_data = {
                        "u_id": friend.u_id,
                        "name": friend.name,
                        "type": "doctor",
                        "specialty": friend.specialty
                    }
                friends_list.append(friend_data)
                
            return jsonify({"friends": friends_list}), 200
            
        doctor = Doctor.query.filter_by(email=user_email).first()
        if doctor:
            # Get doctor's friends (only patients)
            patient_friends = Friendship.query.filter_by(
                user_id=doctor.u_id,
                user_type='doctor'
            ).all()
            
            friends_list = [{
                "u_id": Patient.query.get(f.friend_id).u_id,
                "name": Patient.query.get(f.friend_id).name,
                "type": "patient",
                "heart_score": Patient.query.get(f.friend_id).heart_score
            } for f in patient_friends]
            
            return jsonify({"friends": friends_list}), 200
            
        return jsonify({"error": "User not found"}), 404
        
    except Exception as e:
        print("Error occurred:", str(e))
        return jsonify({"error": str(e)}), 500

# Friend Removal
@app.route('/remove_friend', methods=['DELETE'])
@jwt_required()
def remove_friend():
    try:
        data = request.get_json()
        current_user_email = get_jwt_identity()

        if not data.get('friend_id') or not data.get('friend_type'):
            return jsonify({"error": "Friend ID and type are required"}), 400

        friend_id = data.get('friend_id')
        friend_type = data.get('friend_type')  # 'patient' or 'doctor'

        # Get current user
        current_user = Patient.query.filter_by(email=current_user_email).first()
        current_user_type = 'patient'
        
        if not current_user:
            current_user = Doctor.query.filter_by(email=current_user_email).first()
            current_user_type = 'doctor'

        if not current_user:
            return jsonify({"error": "Current user not found"}), 404

        # Find and remove both friendship records
        friendship1 = Friendship.query.filter_by(
            user_id=current_user.u_id,
            friend_id=friend_id,
            user_type=current_user_type,
            friend_type=friend_type
        ).first()

        friendship2 = Friendship.query.filter_by(
            user_id=friend_id,
            friend_id=current_user.u_id,
            user_type=friend_type,
            friend_type=current_user_type
        ).first()

        if not friendship1 or not friendship2:
            return jsonify({"error": "Friendship not found"}), 404

        db.session.delete(friendship1)
        db.session.delete(friendship2)
        db.session.commit()

        return jsonify({"message": "Friend removed successfully"}), 200

    except Exception as e:
        db.session.rollback()
        print("Error occurred:", str(e))
        return jsonify({"error": str(e)}), 500

# Get All Users
@app.route('/list_users', methods=['GET'])
@jwt_required()
def list_users():
    current_user_email = get_jwt_identity()
    
    # First determine if current user is doctor or patient
    current_user_doctor = Doctor.query.filter_by(email=current_user_email).first()
    current_user_patient = Patient.query.filter_by(email=current_user_email).first()
    
    if not (current_user_doctor or current_user_patient):
        return jsonify({"error": "User not found"}), 404
    
    # Get current user's ID and type
    current_user_id = current_user_doctor.u_id if current_user_doctor else current_user_patient.u_id
    current_user_type = 'doctor' if current_user_doctor else 'patient'
    
    # Get existing friends
    existing_friends = Friendship.query.filter_by(
        user_id=current_user_id,
        user_type=current_user_type
    ).all()
    
    # Create a set of friend IDs and types for efficient lookup
    friend_identifiers = {(friendship.friend_id, friendship.friend_type) for friendship in existing_friends}
    
    users = []
    
    if current_user_doctor:
        # Doctors can only see patients
        patients = Patient.query.all()
        for patient in patients:
            # Don't include self and don't include existing friends
            if patient.email != current_user_email and (patient.u_id, 'patient') not in friend_identifiers:
                users.append({
                    "u_id": patient.u_id,
                    "name": patient.name,
                    "email": patient.email,
                    "type": "patient",
                    "heart_score": patient.heart_score
                })
    elif current_user_patient:
        # Patients can see both doctors and other patients
        doctors = Doctor.query.all()
        patients = Patient.query.all()
        
        # Add doctors who are not already friends
        for doctor in doctors:
            if doctor.email != current_user_email and (doctor.u_id, 'doctor') not in friend_identifiers:
                users.append({
                    "u_id": doctor.u_id,
                    "name": doctor.name,
                    "email": doctor.email,
                    "type": "doctor",
                    "specialty": doctor.specialty
                })
        
        # Add patients who are not already friends
        for patient in patients:
            if patient.email != current_user_email and (patient.u_id, 'patient') not in friend_identifiers:
                users.append({
                    "u_id": patient.u_id,
                    "name": patient.name,
                    "email": patient.email,
                    "type": "patient",
                    "heart_score": patient.heart_score
                })
    
    return jsonify({"users": users})

@app.route('/get_user_type', methods=['GET'])
@jwt_required()
def get_user_type():
    try:
        current_user_email = get_jwt_identity()
        
        # Check if user is a patient
        patient = Patient.query.filter_by(email=current_user_email).first()
        if patient:
            return jsonify({"user_type": "patient"})
            
        # Check if user is a doctor
        doctor = Doctor.query.filter_by(email=current_user_email).first()
        if doctor:
            return jsonify({"user_type": "doctor"})
            
        return jsonify({"error": "User type not found"}), 404
            
    except Exception as e:
        print("Error occurred:", str(e))
        return jsonify({"error": str(e)}), 500
    
def get_user_type_from_email(email):
    """Determine if an email belongs to a patient or doctor"""
    # Check if user is a patient
    patient = Patient.query.filter_by(email=email).first()
    if patient:
        return "patient"
        
    # Check if user is a doctor
    doctor = Doctor.query.filter_by(email=email).first()
    if doctor:
        return "doctor"
        
    return None
############################################################################################################################

# Heart Score Calculation

@app.route('/submit-test', methods=['POST'])
@jwt_required()  # Ensure the user is authenticated
def submit_test():
    try:
        # Extract the data from the incoming request
        data = request.get_json()

        # Ensure the required fields are in the request
        if not data:
            return jsonify({"error": "No data provided"}), 400

        heartHealthRating = data.get('heartHealthRating')
        if heartHealthRating is None:
            return jsonify({"error": "Missing 'heartHealthRating'"}), 400

        walked5000Steps = 10 if data.get('walked5000Steps') == 'Yes' else 0
        lipidPanel = 15 if data.get('lipidPanel') == 'Yes' else 0
        glucoseTest = 15 if data.get('glucoseTest') == 'Yes' else 0
        consultedCardiologist = 20 if data.get('consultedCardiologist') == 'Yes' else 0
        consultedDietitian = 20 if data.get('consultedDietitian') == 'Yes' else 0
        phone_number = data.get('phoneNumber')

        # Extract user email from the JWT token (authentication)
        user_email = get_jwt_identity()

        # Fetch the patient record from the database using the email from the token
        patient = Patient.query.filter_by(email=str(user_email)).first()

        if not patient:
            return jsonify({"error": "User email not found: " + str(user_email)}), 404  # Return 404 if user doesn't exist

        # Calculate the heart score
        heart_score = (
            heartHealthRating * 5
            + walked5000Steps
            + lipidPanel
            + glucoseTest
            + consultedCardiologist
            + consultedDietitian
        )
        heart_score = min(heart_score, 100)  # Ensure the score is capped at 100

        # Update the patient's heart score in the database
        patient.heart_score = heart_score
        patient.phone_number = phone_number
        
        db.session.commit()

        return jsonify({"message": "Test submitted successfully", "heart_score": heart_score}), 200

    except SQLAlchemyError as e:
        # Handle database errors
        db.session.rollback()  # Rollback any transaction to avoid inconsistent states
        return jsonify({"error": f"Database error: {str(e)}"}), 500

    except Exception as e:
        # Handle any other unforeseen errors
        return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500


# Get patient info 
@app.route('/get_patient', methods=['GET'])
@jwt_required()
def get_patient_data():
    # Get the email from the JWT token for verification
    user_email = get_jwt_identity()
    
    # First check if Fitbit token exists and fetch data if needed
    try:
        with open(TOKEN_FILE_PATH, "r") as file:
            tokens = json.load(file)
            
        fitbit_user = tokens.get('user')
        if fitbit_user == user_email:
            # Fetch the latest data from Fitbit
            get_fitbit_data(2)
    except (FileNotFoundError, KeyError):
        # Token file doesn't exist or doesn't contain user key
        # print('here ib p')
        pass
        
    # Retrieve patient data
    patient = Patient.query.filter_by(email=user_email).first()
    if not patient:
        return jsonify({"error": "Patient not found"}), 404
    
    # Calculate and update heart score
    new_score = calculate_heart_score(patient)

    update_user_progress(patient.email, patient.name, patient.heart_score, new_score)
    
    # Only update if the score has changed
    if new_score != patient.heart_score:
        patient.heart_score = new_score
        db.session.commit()
    
    return jsonify({
        "patient": {
            "name": patient.name,
            "heart_score": patient.heart_score,
            "steps": patient.steps,
            "sleep": patient.sleep,
            "breathing_rate": patient.breathing_rate,
            "spo2": patient.spo2,
            "email": patient.email,
            "password": patient.password,
            "u_id": patient.u_id
        }
    }), 200

# Get doctor info
@app.route('/get_doctor', methods=['GET'])
@jwt_required()
def get_doctor():
    # Get user email from JWT token
    user_email = get_jwt_identity()
    
    # Verify this user is requesting their own data
    doctor = Doctor.query.filter_by(email=user_email).first()
    if not doctor:
        return jsonify({"error": "Doctor not found"}), 404

    return jsonify({
        "doctor": {
            "u_id": doctor.u_id,
            "name": doctor.name,
            "email": doctor.email,
            "specialty": doctor.specialty if hasattr(doctor, 'specialty') else None,
            "password": doctor.password
        }
    }), 200


# Doctor Updating Patients Score

@app.route('/doctor/update_health_score', methods=['PUT'])
@jwt_required()
def update_health_score():
    current_user_email = get_jwt_identity()
    doctor = Doctor.query.filter_by(email=current_user_email).first()
    
    if not doctor:
        return jsonify({'error': 'Unauthorized access'}), 403

    data = request.get_json()
    patient_id = data.get('patient_id')
    new_score = data.get('health_score')

    if not patient_id or new_score is None:
        return jsonify({'error': 'Missing required data'}), 400

    patient = Patient.query.get(patient_id)
    
    if not patient:
        return jsonify({'error': 'Patient not found'}), 404
    
    patient.heart_score = new_score
    db.session.commit()

    notify_update(patient.email, patient.name, doctor.name)

    return jsonify({'message': f"Updated health score for {patient.name} to {new_score}"}), 200


@app.route('/doctor/files/<int:patient_id>', methods=['GET', 'OPTIONS'])
@jwt_required(optional=True)
def doctor_list_patient_files(patient_id):
    # For preflight requests, return early without JWT verification.
    if request.method == 'OPTIONS':
        return jsonify({}), 200

    # Now enforce that a token must be present.
    current_user = get_jwt_identity()
    if not current_user:
        return jsonify({"error": "Missing token"}), 401

    doctor = Doctor.query.filter_by(email=current_user).first()
    if not doctor:
        return jsonify({"error": "Unauthorized access"}), 403

    user_folder = os.path.join(app.config['UPLOAD_FOLDER'], str(patient_id))
    if not os.path.exists(user_folder):
        return jsonify({"files": []}), 200

    files = os.listdir(user_folder)
    return jsonify({"files": files}), 200



# Logout User  
@app.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    response = jsonify({"message": "Successfully logged out"})
    unset_jwt_cookies(response)
    return response, 200

########################################################################################################################

# Health Data Upload API 

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/upload', methods=['POST'])
@jwt_required()
def upload_file():
    user_email = get_jwt_identity()
    patient = Patient.query.filter_by(email=str(user_email)).first()

    if not patient:
        return jsonify({"error": "Patient not found"}), 404

    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400

    file = request.files['file']
    if not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file type. Only PDF and DOCX files are allowed.'}), 400

    u_id = patient.u_id  # Get user ID
    user_folder = os.path.join(app.config['UPLOAD_FOLDER'], str(u_id))
    os.makedirs(user_folder, exist_ok=True)

    filename = secure_filename(file.filename)
    file_path = os.path.join(user_folder, filename)
    
    file.save(file_path)

    return jsonify({'message': 'File uploaded successfully', 'filename': filename})

@app.route('/files', methods=['GET'])
@jwt_required()
def list_files():
    user_email = get_jwt_identity()
    patient = Patient.query.filter_by(email=str(user_email)).first()

    if not patient:
        return jsonify({"error": "Patient not found"}), 404

    u_id = patient.u_id
    user_folder = os.path.join(app.config['UPLOAD_FOLDER'], str(u_id))

    if not os.path.exists(user_folder):
        return jsonify({'files': []})

    files = os.listdir(user_folder)

    return jsonify({'files': files})

@app.route('/files/<filename>', methods=['GET'])
@jwt_required()
def get_file(filename):
    user_email = get_jwt_identity()
    patient = Patient.query.filter_by(email=str(user_email)).first()
    
    if not patient:
        return jsonify({"error": "Patient not found"}), 404
        
    u_id = patient.u_id
    user_folder = os.path.join(app.config['UPLOAD_FOLDER'], str(u_id))
    
    try:
        return send_from_directory(user_folder, filename)
    except FileNotFoundError:
        return jsonify({"error": "File not found"}), 404


@app.route('/files/<filename>', methods=['DELETE'])
@jwt_required()
def delete_file(filename):
    user_email = get_jwt_identity()
    patient = Patient.query.filter_by(email=str(user_email)).first()
    
    if not patient:
        return jsonify({"error": "Patient not found"}), 404
        
    u_id = patient.u_id
    user_folder = os.path.join(app.config['UPLOAD_FOLDER'], str(u_id))
    file_path = os.path.join(user_folder, filename)
    
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            return jsonify({"message": "File deleted successfully"}), 200
        else:
            return jsonify({"error": "File not found"}), 404
    except Exception as e:
        return jsonify({"error": f"Error deleting file: {str(e)}"}), 500
###############################################################################################################

# Fitbit API Integration
@app.route('/connect_watch', methods=['GET'])
@jwt_required()
def connect_watch():
    # Generate a random code verifier and challenge
    flag = False
    try:
        with open(TOKEN_FILE_PATH, "r") as file:
            tokens = json.load(file)

        url = "https://api.fitbit.com/1.1/oauth2/introspect"
        introspect_response = requests.post(url, headers={
            'Authorization': 'Bearer ' + tokens['access_token'],
            'Accept': 'application/x-www-form-urlencoded',
            'Accept-Language': 'en_US'
        }, 
        data={
            'token': tokens['access_token']
        })
        if introspect_response.status_code == 200:
            if introspect_response.json()['active'] and tokens['user'] == get_jwt_identity():
                flag = True
                print("Fitbit token is valid")
            else:
                print("Fitbit token is not valid")
        else:
            print("Failed to introspect token", introspect_response.json())
    except Exception as e:
        # Token file doesn't exist
        pass

    if os.environ.get("state") == '' and not flag:
        verifier = base64.b64encode(os.urandom(32)).decode().rstrip("=")
        challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).decode().rstrip("=")
        os.environ["state"] = verifier
    else:
        return jsonify({"error": "Already connected to Fitbit", "status": "SKIP"})
        # verifier = os.environ.get("state")
        # challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).decode().rstrip("=")
    print("State: ", verifier, challenge)
    # session['state'] = verifier
    os.environ['fitbit_user'] = get_jwt_identity()
    # os.environ["code_verifier"] = code_verifier Dont need this anymore        
    # Return the code_challenge and client_id to the frontend
    client_id = os.getenv("CLIENT_ID")
    return jsonify({
        'code_challenge': challenge,
        'code_challenge_method': 'S256',
        'client_id': client_id
    })

@app.route('/watch', methods=['GET'])
def callback():
    # Get the authorization code from the query parameters
    code = request.args.get('code')
    if not code:
        return jsonify({"error": "Authorization code not found"}), 400
    
    # Retrieve the stored code_verifier
    # code_verifier = os.environ.get("code_verifier")
    # if not code_verifier:
    #     return jsonify({"error": "Code verifier not found"}), 400
    # print(code)
    # Prepare the token request payload
    client_id = os.environ.get("CLIENT_ID")
    client_secret = os.environ.get("CLIENT_SECRET")
    # redirect_uri = os.getenv("FITBIT_REDIRECT_URI")
    url = "https://api.fitbit.com/oauth2/token"
    verifier = os.environ.get("state")
    print("Verifier: "+ verifier)
    token_response = requests.post(url, data={
        'client_id': client_id,
        'grant_type': 'authorization_code',
        'code': code,
        'code_verifier': verifier,
        'redirect_uri': os.getenv("FITBIT_REDIRECT_URI")
    },
    headers={
        'Authorization': 'Basic ' + base64.b64encode(f"{client_id}:{client_secret}".encode()).decode(),
        'Content-Type': 'application/x-www-form-urlencoded'
    })
    if token_response.status_code == 200:
        USER = os.environ.get("fitbit_user")
        print("Fitbit User: ",USER)
        access_token = token_response.json()['access_token']
        refresh_token = token_response.json()['refresh_token']
        with open(TOKEN_FILE_PATH, "w") as file:
            json.dump({'access_token': access_token, 'refresh_token': refresh_token, 'user': USER}, file)
        print("Successfully connected to Fitbit")
        return redirect("http://localhost:3000/patient-dashboard") # Change this to 3000 for the frontend
    else:
        os.environ["fitbit_user"] = ''
        USER = ''
        os.environ["state"] = ''
        print("Failed to connect to Fitbit", token_response.json(), token_response.status_code)
        return jsonify({"error": "Failed to connect to Fitbit"}), 500


def get_fitbit_data(tries=1):
    with open(TOKEN_FILE_PATH, "r") as file:
        tokens = json.load(file)

    print("Fetching Fitbit data...")
    patient = Patient.query.filter_by(email=tokens['user']).first()
    access_token = tokens['access_token'] 
    url_list = ["https://api.fitbit.com/1/user/-/activities/heart/date/today/1d/5min.json", "https://api.fitbit.com/1/user/-/activities/steps/date/today/1d.json", "https://api.fitbit.com/1/user/-/br/date/today/all.json", "https://api.fitbit.com/1/user/-/spo2/date/today.json", f"https://api.fitbit.com/1/user/-/ecg/list.json?afterDate={datetime.datetime.today().date()}&sort=asc&limit=1&offset=0", f"https://api.fitbit.com/1.2/user/-/sleep/date/{datetime.datetime.today().date()}.json"]
    responses = []
    for url in url_list:
        response = requests.get(url, headers={
            'Authorization': f'Bearer {access_token}',
            'Accept': 'application/json',
            'Accept-Language': 'en_US'
        })
        print(url, response.status_code)
        if response.status_code == 200:
            data = response.json()
            # print(data)
            if 'heart' in url:
                try:
                    heart_rate = data['activities-heart-intraday']['dataset'][-1]['value']
                    patient.avg_heartrate = heart_rate
                    db.session.commit()
                    # print(heart_rate)
                    responses.append((jsonify({"message": "Data fetched successfully"}), 200))
                except:
                    db.session.rollback()
                    responses.append((jsonify({"error": "Data not present"}), 290))
            elif 'steps' in url:
                # print('here')
                try:
                    steps = data['activities-steps'][0]['value']
                    # Store in daily steps
                    patient.steps = steps
                    db.session.commit()
                    responses.append((jsonify({"message": "Data fetched successfully"}), 200))
                except:
                    db.session.rollback()
                    responses.append(( jsonify({"error": "Data not present"}), 290))

            elif 'br' in url:
                # print('Breathing Rate:', data['br'][0]['value']['breathingRate'])
                try:
                    breating_rate = data['br'][0]['value']['fullSleepSummary']['breathingRate']
                    patient.breathing_rate = breating_rate
                    print('Breathing Rate:', breating_rate)
                    db.session.commit()
                    responses.append((jsonify({"message": "Data fetched successfully"}), 200))
                except:
                    db.session.rollback()
                    responses.append((jsonify({"error": "Data not present"}), 290))
            elif 'spo2' in url:
                # print('Spo2:', data['value']['avg'])
                try:
                    spo2 = data['value']['avg']
                    patient.spo2 = spo2
                    print("Spo2: ", spo2)
                    db.session.commit()
                    responses.append((jsonify({"message": "Data fetched successfully"}), 200))
                except:
                    db.session.rollback()
                    responses.append((jsonify({"error": "Data not present"}), 290))
            elif 'ecg' in url:
                # print('ECG:', data['ecgReadings'][0]['resultClassification'])
                try:
                    ecg = data['ecgReadings'][0]['resultClassification']
                    patient.ecg = ecg
                    print("ECG: ", ecg)
                    db.session.commit()
                    responses.append((jsonify({"message": "Data fetched successfully"}), 200))
                except:
                    db.session.rollback()
                    responses.append((jsonify({"error": "Data not present"}), 290))
            elif 'sleep' in url:
                try:
                    sleep = data['sleep'][0]['minutesAsleep']
                    patient.sleep = sleep
                    # print("Sleep: ", sleep)
                    db.session.commit()
                    responses.append((jsonify({"message": "Data fetched successfully"}), 200))
                except:
                    db.session.rollback()
                    responses.append((jsonify({"error": "Data not present"}), 290))
            # elif 'profile' in url:
            #     try:
            #         weight = str(data['weight'])+str(data['weightUnit'])
            #         height = str(data['height'])+str(data['heightUnit'])
            #         patient.weight = name
            #         db.session.commit()
            #         return jsonify({"message": "Data fetched successfully"}), 200
            #     except:
            #         return jsonify({"error": "Data not present"}), 290
        else:
            if response.status_code == 401:
                access_token = Get_New_Access_Token(os.getenv("CLIENT_ID"), os.getenv("CLIENT_SECRET"))
                if access_token and tries > 0:
                    return get_fitbit_data(tries - 1)
            return jsonify({"error": "Failed to fetch data from Fitbit", "url": url}), 500
    return responses

# In refresh_fitbit_tokens function
def refresh_fitbit_tokens(client_id, client_secret, refresh_token):
    print("Attempting to refresh tokens...")
    try:
        url = "https://api.fitbit.com/oauth2/token"
        headers = {
            "Authorization": "Basic " + base64.b64encode((client_id + ":" + client_secret).encode()).decode(),
            "Content-Type": "application/x-www-form-urlencoded"
        }
        data = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token
        }
        json_data = requests.post(url, headers=headers, data=data)
        if json_data.status_code != 200 or "access_token" not in json_data.json():
            print("Failed to refresh Fitbit tokens", json_data.json(), json_data.status_code)
            return None, None
        print(json_data)
        access_token = json_data["access_token"]
        new_refresh_token = json_data["refresh_token"]
        tokens = {
            "access_token": access_token,
            "refresh_token": new_refresh_token
        }
        with open(TOKEN_FILE_PATH, "w") as file:
            json.dump(tokens, file)
        print("Fitbit token refresh successful!")
        return access_token, new_refresh_token
    except Exception as e:
        print("Error refreshing Fitbit tokens:", str(e))
        return None, None


def load_tokens_from_file():
    with open(TOKEN_FILE_PATH, "r") as file:
        tokens = json.load(file)
        return tokens.get("access_token"), tokens.get("refresh_token")

def Get_New_Access_Token(client_id, client_secret):
    try:
        access_token, refresh_token = load_tokens_from_file()
    except FileNotFoundError:
        refresh_token = input("No token file found. Please enter a valid refresh token : ")
    access_token, refresh_token = refresh_fitbit_tokens(client_id, client_secret, refresh_token)
    return access_token

########################################################################################################################
def calculate_heart_score(patient, fitbit_data=None):
    """
    Calculate a comprehensive heart score based on:
    1. Previous heart score (weighted less over time)
    2. Average heart rate (compared to age-based healthy ranges)
    3. Daily steps (compared to recommended 10,000 steps)
    4. Sleep duration (compared to recommended 7-9 hours)
    5. Breathing rate (compared to normal range of 12-20 breaths/min)
    6. SpO2 levels (compared to healthy range of 95-100%)
    7. ECG readings (normal vs abnormal)
    
    Returns a score from 0-100
    """
    # Start with base score or previous score
    previous_score = patient.heart_score if patient.heart_score else 50
    
    # Define weights for different factors
    weights = {
        'previous_score': 0.3,  # Previous score weight decreases over time
        'heart_rate': 0.15,
        'steps': 0.15,
        'sleep': 0.15,
        'breathing_rate': 0.1,
        'spo2': 0.1,
        'ecg': 0.05
    }
    
    # Calculate component scores
    scores = {}
    
    # Previous score component
    scores['previous_score'] = previous_score
    
    # Heart rate component (normal resting is typically 60-100 bpm)
    avg_heart_rate = patient.avg_heartrate
    if avg_heart_rate:
        if avg_heart_rate < 60:
            # Unusually low - score linearly from 50-80
            scores['heart_rate'] = max(50, 80 - (60 - avg_heart_rate) * 2)
        elif 60 <= avg_heart_rate <= 70:
            # Excellent range
            scores['heart_rate'] = 100
        elif 70 < avg_heart_rate <= 80:
            # Very good range
            scores['heart_rate'] = 90
        elif 80 < avg_heart_rate <= 90:
            # Good range
            scores['heart_rate'] = 80
        elif 90 < avg_heart_rate <= 100:
            # Normal range
            scores['heart_rate'] = 70
        else:
            # Above normal - score decreases as heart rate increases
            scores['heart_rate'] = max(0, 70 - (avg_heart_rate - 100) * 1.5)
    else:
        scores['heart_rate'] = 50  # Default if no data
    
    # Steps component (10,000 steps is recommended)
    steps = patient.steps
    if steps:
        scores['steps'] = min(100, steps / 100)  # 10,000 steps = 100 points
    else:
        scores['steps'] = 50  # Default if no data
    
    # Sleep component (7-9 hours recommended)
    sleep_minutes = patient.sleep
    if sleep_minutes:
        sleep_hours = sleep_minutes / 60
        if 7 <= sleep_hours <= 9:
            # Optimal range
            scores['sleep'] = 100
        elif 6 <= sleep_hours < 7 or 9 < sleep_hours <= 10:
            # Good range
            scores['sleep'] = 80
        elif 5 <= sleep_hours < 6 or 10 < sleep_hours <= 11:
            # Fair range
            scores['sleep'] = 60
        else:
            # Poor range
            scores['sleep'] = 40
    else:
        scores['sleep'] = 50  # Default if no data
    
    # Breathing rate component (12-20 breaths/min is normal)
    breathing_rate = patient.breathing_rate
    if breathing_rate:
        if 12 <= breathing_rate <= 20:
            # Normal range
            scores['breathing_rate'] = 100
        elif 10 <= breathing_rate < 12 or 20 < breathing_rate <= 22:
            # Slightly outside normal range
            scores['breathing_rate'] = 80
        elif 8 <= breathing_rate < 10 or 22 < breathing_rate <= 25:
            # Moderately outside normal range
            scores['breathing_rate'] = 60
        else:
            # Significantly outside normal range
            scores['breathing_rate'] = 40
    else:
        scores['breathing_rate'] = 50  # Default if no data
    
    # SpO2 component (95-100% is normal)
    spo2 = patient.spo2
    if spo2:
        if 95 <= spo2 <= 100:
            # Normal range
            scores['spo2'] = 100
        elif 90 <= spo2 < 95:
            # Mild hypoxemia
            scores['spo2'] = 70
        elif 85 <= spo2 < 90:
            # Moderate hypoxemia
            scores['spo2'] = 40
        else:
            # Severe hypoxemia
            scores['spo2'] = 10
    else:
        scores['spo2'] = 50  # Default if no data
    
    # ECG component
    ecg = patient.ecg
    if ecg:
        if ecg == "Normal":
            scores['ecg'] = 100
        elif ecg == "Inconclusive":
            scores['ecg'] = 60
        else:
            # Any abnormal reading
            scores['ecg'] = 0
    else:
        scores['ecg'] = 50  # Default if no data
    
    # Calculate weighted score
    final_score = sum(scores[key] * weights[key] for key in weights)
    
    # Round to nearest integer
    return round(final_score)

########################################################################################################################
# Email sending logic

def welcome_user(email, name):
    gmail_user = "superhear.csc301@gmail.com"
    gmail_pass = os.getenv("gmail_pass")

    msg = EmailMessage()
    msg["From"] = gmail_user
    msg["To"] = email
    msg["Subject"] = "Welcome to Super Heart!"

    html_content = f"""
    <html>
    <head>
        <style>
            body {{
                font-family: Arial, sans-serif;
                line-height: 1.5;
                color: #333;
            }}
            h1 {{
                color: #d22;
            }}
            a {{
                color: #007bff;
            }}
        </style>
    </head>
    <body>
        <h1>Welcome to Super Heart, {name}!</h1>
        <p>We're excited to have you on board. Here's what you can do next:</p>
        <ul>
            <li>Check your heart score insights.</li>
            <li>Track your daily steps.</li>
            <li>Connect with Fitbit to gain a more detailed view of your health data.</li>
        </ul>
        <h6>Welcome to Costco, I love you</h6>
        <p><strong>Best,</strong><br>The Super Heart Team</p>
    </body>
    </html>
    """

    msg.set_content("Your email client does not support HTML.")
    msg.add_alternative(html_content, subtype="html")

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(gmail_user, gmail_pass)
            server.send_message(msg)
        print("Email sent successfully!")
    except Exception as e:
        print(f"Error: Sending email failed! Details: {e}")

def notify_user(email, name):
    gmail_user = "superhear.csc301@gmail.com"
    gmail_pass = os.getenv("gmail_pass")

    subject = "Your Account Info Was Updated"

    html_body = f"""\
    <html>
    <head>
        <style>
            body {{
                font-family: Arial, sans-serif;
                background-color: #f9f9f9;
                color: #333;
                line-height: 1.6;
                text-align: center;
            }}
            .container {{
                width: 90%;
                max-width: 600px;
                margin: auto;
                background: #fff;
                padding: 20px;
                border-radius: 8px;
                box-shadow: 0px 0px 10px rgba(0, 0, 0, 0.1);
            }}
            h1 {{
                color: #d22;
                font-size: 22px;
            }}
            p {{
                font-size: 16px;
            }}
            .btn {{
                display: inline-block;
                background: #007bff;
                color: #fff;
                text-decoration: none;
                padding: 12px 20px;
                border-radius: 5px;
                margin-top: 20px;
                font-weight: bold;
            }}
            .btn:hover {{
                background: #0056b3;
            }}
            .footer {{
                margin-top: 20px;
                font-size: 12px;
                color: #666;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Hello {name},</h1>
            <p>Your account information has been successfully updated.</p>
            <p>If you did not make this change, please contact support immediately.</p>
            <p class="footer">Super Heart | Keeping your heart in check ❤️</p>
        </div>
    </body>
    </html>
    """

    em = EmailMessage()
    em["From"] = gmail_user
    em["To"] = email
    em["Subject"] = subject

    em.add_alternative(html_body, subtype="html")

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(gmail_user, gmail_pass)
            smtp.send_message(em)
    except Exception as e:
        print(f"Error: Sending email failed! Details: {e}")

def update_user_progress(email, name, old_score, new_score):
    gmail_user = "superhear.csc301@gmail.com"
    gmail_pass = os.getenv("gmail_pass")

    msg = EmailMessage()
    msg["From"] = gmail_user
    msg["To"] = email
    msg["Subject"] = "Your Progress Update from Super Heart!"

    # HTML Content based on score change
    if new_score > old_score:
        html_content = f"""
        <html>
        <head>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.5;
                    color: #333;
                }}
                h1 {{
                    color: #4caf50;
                }}
                p {{
                    font-size: 16px;
                }}
                .congrats {{
                    color: #4caf50;
                    font-weight: bold;
                }}
                .encouragement {{
                    color: #d22;
                    font-weight: bold;
                }}
            </style>
        </head>
        <body>
            <h1>Congratulations, {name}!</h1>
            <p>Your score has improved from <strong>{old_score}</strong> to <strong>{new_score}</strong>.</p>
            <p class="congrats">Great job! Keep up the good work and continue staying active to maintain this awesome progress.</p>
            <p>We're proud of your efforts!</p>
            <p><strong>Best regards,</strong><br>The Super Heart Team</p>
        </body>
        </html>
        """
        msg.set_content("Your email client does not support HTML.")
        msg.add_alternative(html_content, subtype="html")

    elif new_score < old_score:
        html_content = f"""
        <html>
        <head>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.5;
                    color: #333;
                }}
                h1 {{
                    color: #d22;
                }}
                p {{
                    font-size: 16px;
                }}
                .congrats {{
                    color: #4caf50;
                    font-weight: bold;
                }}
                .encouragement {{
                    color: #d22;
                    font-weight: bold;
                }}
            </style>
        </head>
        <body>
            <h1>Hey {name},</h1>
            <p>Your score has dropped from <strong>{old_score}</strong> to <strong>{new_score}</strong>.</p>
            <p class="encouragement">Don't worry! It's normal to have ups and downs, but remember: the most important part is to keep trying and staying active!</p>
            <p>We believe in your potential! Keep up the effort, and you’ll be back on track in no time!!!</p>

            <h6>p.s, put down the ice cream eh?</h6>
            <p><strong>Best regards,</strong><br>The Super Heart Team</p>
        </body>
        </html>
        """
        msg.set_content("Your email client does not support HTML.")
        msg.add_alternative(html_content, subtype="html")
    
    else:
        return

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(gmail_user, gmail_pass)
            server.send_message(msg)
        print("Progress update email sent successfully!")
    except Exception as e:
        print(f"Error: Sending progress update email failed! Details: {e}")

def notify_update(patient_email, patient_name, doctor_name):
    gmail_user = "superhear.csc301@gmail.com"
    gmail_pass = os.getenv("gmail_pass")

    msg = EmailMessage()
    msg["From"] = gmail_user
    msg["To"] = patient_email
    msg["Subject"] = "Your Heart Score Has Just Been Updated By a Doctor"

    html_content = f"""
    <html>
    <head>
        <style>
            body {{
                font-family: Arial, sans-serif;
                line-height: 1.5;
                color: #333;
            }}
            h1 {{
                color: #007bff;
            }}
            p {{
                font-size: 16px;
            }}
            .doctor {{
                font-weight: bold;
                color: #d22;
            }}
            .cta {{
                margin-top: 20px;
                padding: 10px;
                background-color: #007bff;
                color: white;
                text-decoration: none;
                display: inline-block;
                border-radius: 5px;
            }}
        </style>
    </head>
    <body>
        <h1>Hello {patient_name},</h1>
        <p>Your heart score has been updated by Dr. <span class="doctor">{doctor_name}</span></p>
        <p>We recommend that you check in with Dr. {doctor_name} to stay informed about your health and what warranted this change.</p>

        <h6>If you believe that this new score is unjust, an amendment can be made by a formal duel request with Dr. {doctor_name}.</h6>
        <p><strong>Best regards,</strong><br>The Super Heart Team</p>
    </body>
    </html>
    """

    msg.set_content("Your email client does not support HTML. Please check your Super Heart dashboard for updates.")
    msg.add_alternative(html_content, subtype="html")

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(gmail_user, gmail_pass)
            server.send_message(msg)
        print("Doctor update notification email sent successfully!")
    except Exception as e:
        print(f"Error: Sending doctor update email failed! Details: {e}")

############################################################################################################################
# Friend request logic
@app.route('/send_friend_request', methods=['POST'])
@jwt_required()
def send_friend_request():
    try:
        # Get the current user's ID and type
        current_user = get_jwt_identity()
        user_type = get_user_type_from_email(current_user)
        
        # Get data from request body
        data = request.get_json()
        
        receiver_id = data.get('receiver_id')
        receiver_type = data.get('receiver_type')
        
        if not receiver_id or not receiver_type:
            return jsonify({'error': 'Missing receiver_id or receiver_type'}), 400
        
        # Get current user ID
        if user_type == 'patient':
            user = Patient.query.filter_by(email=current_user).first()
        else:
            user = Doctor.query.filter_by(email=current_user).first()
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Check if an active request already exists
        existing_request = FriendRequest.query.filter(
            ((FriendRequest.sender_id == user.u_id) & (FriendRequest.sender_type == user_type) &
             (FriendRequest.receiver_id == receiver_id) & (FriendRequest.receiver_type == receiver_type)) |
            ((FriendRequest.sender_id == receiver_id) & (FriendRequest.sender_type == receiver_type) &
             (FriendRequest.receiver_id == user.u_id) & (FriendRequest.receiver_type == user_type)),
            FriendRequest.status == 'pending'  # Only consider pending requests
        ).first()
        
        if existing_request:
            return jsonify({'error': 'Friend request already exists', 'status': 'existing_request'}), 400
        
        # Check if already friends
        existing_friendship = Friendship.query.filter(
            ((Friendship.user_id == user.u_id) & (Friendship.user_type == user_type) &
             (Friendship.friend_id == receiver_id) & (Friendship.friend_type == receiver_type)) |
            ((Friendship.user_id == receiver_id) & (Friendship.user_type == receiver_type) &
             (Friendship.friend_id == user.u_id) & (Friendship.friend_type == user_type))
        ).first()
        
        if existing_friendship:
            return jsonify({'error': 'You are already friends', 'status': 'already_friends'}), 400
        
        # Create and save the friend request
        friend_request = FriendRequest(
            sender_id=user.u_id,
            sender_type=user_type,
            receiver_id=receiver_id,
            receiver_type=receiver_type,
            status='pending'
        )
        
        db.session.add(friend_request)
        db.session.commit()
        
        return jsonify({'message': 'Friend request sent successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# List friend requests
@app.route('/list_friend_requests', methods=['GET'])
@jwt_required()
def list_friend_requests():
    try:
        # Get the current user's ID and type
        current_user = get_jwt_identity()
        user_type = get_user_type_from_email(current_user)
        
        if user_type == 'patient':
            user = Patient.query.filter_by(email=current_user).first()
        else:
            user = Doctor.query.filter_by(email=current_user).first()
        
        # Get incoming friend requests
        incoming_requests = FriendRequest.query.filter_by(
            receiver_id=user.u_id, 
            receiver_type=user_type,
            status='pending'
        ).all()
        
        # Get outgoing friend requests
        outgoing_requests = FriendRequest.query.filter_by(
            sender_id=user.u_id,
            sender_type=user_type,
            status='pending'
        ).all()
        
        incoming_list = []
        for request in incoming_requests:
            if request.sender_type == 'patient':
                sender = Patient.query.filter_by(u_id=request.sender_id).first()
                heart_score = sender.heart_score
                specialty = None
            else:
                sender = Doctor.query.filter_by(u_id=request.sender_id).first()
                heart_score = None
                specialty = sender.specialty
                
            incoming_list.append({
                'request_id': request.id,
                'u_id': sender.u_id,
                'name': sender.name,
                'email': sender.email,
                'type': request.sender_type,
                'heart_score': heart_score,
                'specialty': specialty
            })
        
        outgoing_list = []
        for request in outgoing_requests:
            if request.receiver_type == 'patient':
                receiver = Patient.query.filter_by(u_id=request.receiver_id).first()
                heart_score = receiver.heart_score
                specialty = None
            else:
                receiver = Doctor.query.filter_by(u_id=request.receiver_id).first()
                heart_score = None
                specialty = receiver.specialty
                
            outgoing_list.append({
                'request_id': request.id,
                'u_id': receiver.u_id,
                'name': receiver.name,
                'email': receiver.email,
                'type': request.receiver_type,
                'heart_score': heart_score,
                'specialty': specialty
            })
        
        return jsonify({
            'incoming_requests': incoming_list,
            'outgoing_requests': outgoing_list
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500



# Accept a friend request
@app.route('/accept_friend_request/<int:request_id>', methods=['POST'])
@jwt_required()
def accept_friend_request(request_id):
    try:
        current_user = get_jwt_identity()
        
        # Find the request
        friend_request = FriendRequest.query.get(request_id)
        
        if not friend_request:
            return jsonify({"error": "Friend request not found"}), 404
        
        # Verify the receiver is the current user
        receiver_id = friend_request.receiver_id
        receiver_type = friend_request.receiver_type
        
        if receiver_type == 'patient':
            receiver = Patient.query.filter_by(u_id=receiver_id).first()
        else:
            receiver = Doctor.query.filter_by(u_id=receiver_id).first()
        
        if not receiver or receiver.email != current_user:
            return jsonify({"error": "Unauthorized to accept this request"}), 403
        
        # Get sender information
        sender_id = friend_request.sender_id
        sender_type = friend_request.sender_type
        
        # Create friendship in both directions
        # First direction: receiver -> sender
        friendship1 = Friendship(
            user_id=receiver_id,
            friend_id=sender_id,
            user_type=receiver_type,
            friend_type=sender_type
        )
        
        # Second direction: sender -> receiver
        friendship2 = Friendship(
            user_id=sender_id,
            friend_id=receiver_id,
            user_type=sender_type,
            friend_type=receiver_type
        )
        
        # Update request status
        friend_request.status = 'accepted'
        
        # Commit all changes
        db.session.add(friendship1)
        db.session.add(friendship2)
        db.session.commit()
        
        return jsonify({"message": "Friend request accepted successfully"}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

# Reject a friend request (modified to also handle cancellation)
@app.route('/reject_friend_request/<int:request_id>', methods=['POST'])
@jwt_required()
def reject_friend_request(request_id):
    try:
        # Get the current user's ID and type
        current_user = get_jwt_identity()
        user_type = get_user_type_from_email(current_user)
        
        if user_type == 'patient':
            user = Patient.query.filter_by(email=current_user).first()
        else:
            user = Doctor.query.filter_by(email=current_user).first()
        
        # Find the friend request (either as receiver or sender)
        friend_request = FriendRequest.query.filter(
            FriendRequest.id == request_id,
            ((FriendRequest.receiver_id == user.u_id) & 
             (FriendRequest.receiver_type == user_type)) |
            ((FriendRequest.sender_id == user.u_id) & 
             (FriendRequest.sender_type == user_type)),
            FriendRequest.status == 'pending'
        ).first()
        
        if not friend_request:
            return jsonify({'error': 'Friend request not found'}), 404
        
        # If user is receiver, mark as rejected
        if friend_request.receiver_id == user.u_id and friend_request.receiver_type == user_type:
            friend_request.status = 'rejected'
            db.session.commit()
            return jsonify({'message': 'Friend request rejected'}), 200
        
        # If user is sender, delete the request
        if friend_request.sender_id == user.u_id and friend_request.sender_type == user_type:
            db.session.delete(friend_request)
            db.session.commit()
            return jsonify({'message': 'Friend request cancelled'}), 200
        
        return jsonify({'error': 'Unauthorized to modify this request'}), 403
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5001)
