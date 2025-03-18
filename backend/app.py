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

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
CORS(app)
app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql://postgres:PostgresHuh@localhost:5432/newDB" # Replace <user>, <password>, <database_name>
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY') # DONT FORGET ABOUT THE .env file that's gitignored
api = Api(app, version='1.0', title='Health API', description='A simple Health API')
# Allowed file extensions
ALLOWED_EXTENSIONS = {'pdf', 'docx'}
UPLOAD_FOLDER = 'uploads'
TOKEN_FILE_PATH = 'fitbit_token.json'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

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
    phone_number = db.Column(db.String(15), nullable=False, unique=True, default="000-000-0000")  # Default phone number
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

        db.session.add(new_user)
        db.session.commit()

        return jsonify({"message": f"{type.capitalize()} registration successful"}), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Registration failed: {str(e)}"}), 500

# Update your login route to check both tables
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    print(data)
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

# @app.route('/protected', methods=['GET'])
# @jwt_required()
# def protected():
#     current_user = get_jwt_identity()

#     # Handle the case where identity is a dict
#     if isinstance(current_user, dict):
#         user_type = current_user.get('type')
#         user_email = current_user.get('email')

#         if user_type == 'doctor':
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

@app.route('/get_weekly_spo2', methods=['GET'])
@jwt_required()
def get_weekly_spo2():
    user_email = get_jwt_identity()
    patient = Patient.query.filter_by(email=user_email).first()
    
    if not patient:
        return jsonify({"error": "Patient not found"}), 404

    try:
        end_date = datetime.date.today()
        start_date = end_date - datetime.timedelta(days=6)
        
        access_token, _ = load_tokens_from_file()
        if not access_token:
            return jsonify({"error": "Fitbit not connected"}), 400

        url = f"https://api.fitbit.com/1/user/-/spo2/date/{start_date}/{end_date}.json"
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

        fitbit_data = response.json().get('spo2', [])
        spo2_dict = {}
        
        # Handle Fitbit's different response structure
        for entry in fitbit_data:
            date = entry['dateTime']
            # Check for both possible response formats
            if 'minutes' in entry['value']:
                # Daily average format
                spo2_dict[date] = entry['value'].get('avg', patient.spo2 or 98.0)
            else:
                # Direct value format
                spo2_dict[date] = entry['value'].get('avg', patient.spo2 or 98.0)
        
        complete_data = []
        for i in range(7):
            date = (end_date - datetime.timedelta(days=6-i)).strftime('%Y-%m-%d')
            complete_data.append({
                "date": date,
                "spo2": spo2_dict.get(date, patient.spo2)
            })

        return jsonify({"weekly_spo2": complete_data}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    

############################################################################################################################
# FRIEND ROUTES
@app.route('/add_friend', methods=['POST'])
@jwt_required()
def add_friend():
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
            
        # Enforce doctor-patient relationship rules
        if current_user_type == 'doctor' and friend_type != 'patient':
            return jsonify({"error": "Doctors can only add patients as friends"}), 400
            
        # Get friend
        if friend_type == 'patient':
            friend = Patient.query.get(friend_id)
        else:
            friend = Doctor.query.get(friend_id)
            
        if not friend:
            return jsonify({"error": "Friend not found"}), 404
            
        if current_user.u_id == friend_id and current_user_type == friend_type:
            return jsonify({"error": "Cannot add yourself as friend"}), 400
            
        # Check if friendship already exists
        existing = Friendship.query.filter_by(
            user_id=current_user.u_id,
            friend_id=friend_id,
            user_type=current_user_type,
            friend_type=friend_type
        ).first()
        
        if existing:
            return jsonify({"error": "Already friends"}), 400
            
        # Create friendship (both ways)
        friendship1 = Friendship(
            user_id=current_user.u_id,
            friend_id=friend_id,
            user_type=current_user_type,
            friend_type=friend_type
        )
        
        # Create reciprocal friendship
        friendship2 = Friendship(
            user_id=friend_id,
            friend_id=current_user.u_id,
            user_type=friend_type,
            friend_type=current_user_type
        )
        
        db.session.add(friendship1)
        db.session.add(friendship2)
        db.session.commit()
        
        return jsonify({"message": "Friend added successfully"}), 201

    except Exception as e:
        print("Error occurred:", str(e))
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

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
    
    users = []
    
    if current_user_doctor:
        # Doctors can only see patients
        patients = Patient.query.all()
        for patient in patients:
            if patient.email != current_user_email:  # Don't include self
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
        
        # Add doctors
        for doctor in doctors:
            if doctor.email != current_user_email:  # Don't include self
                users.append({
                    "u_id": doctor.u_id,
                    "name": doctor.name,
                    "email": doctor.email,
                    "type": "doctor",
                    "specialty": doctor.specialty
                })
        
        # Add patients
        for patient in patients:
            # Don't include self and check if patient ID is same as any doctor ID
            if patient.email != current_user_email:
                # Check if this patient's ID matches any doctor's ID we've already added
                is_duplicate_id = any(
                    user["u_id"] == patient.u_id and user["type"] == "doctor" 
                    for user in users
                )
                
                # Only add if it's not a duplicate ID
                if not is_duplicate_id:
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
    
    if os.getenv('fitbit_user') == user_email:
        response = get_fitbit_data(2)
        print(response)
        # if response[1] != 200:
        #     print("Failed to fetch Fitbit data/ Data is invalid")
        # else:
        #     print("Fitbit data fetched successfully")
    # else:
    #     print("User email:", user_email)
    # Verify this user is requesting their own data
    patient = Patient.query.filter_by(email=str(user_email)).first()
    if not patient:
        return jsonify({"error": "Patient not found"}), 404

    return jsonify({
        "patient": {
            "name": patient.name,
            "heart_score": patient.heart_score,
            "steps": patient.steps,
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
            "specialty": doctor.specialty if hasattr(doctor, 'specialty') else None
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
    # Generate a random code_verifier
    code_verifier = base64.urlsafe_b64encode(os.urandom(32)).decode().rstrip("=")
    
    # Generate the code_challenge using SHA-256
    code_challenge = base64.urlsafe_b64encode(
        hashlib.sha256(code_verifier.encode()).digest()
    ).decode().rstrip("=")
    
    # Store the code_verifier in the environment or session
    os.environ["code_verifier"] = code_verifier
    os.environ["fitbit_user"] = get_jwt_identity()
    
    # Return the code_challenge and client_id to the frontend
    client_id = os.getenv("CLIENT_ID")
    return jsonify({
        'code_challenge': code_challenge,
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
    code_verifier = os.environ.get("code_verifier")
    if not code_verifier:
        return jsonify({"error": "Code verifier not found"}), 400
    
    # Prepare the token request payload
    client_id = os.getenv("CLIENT_ID")
    client_secret = os.getenv("CLIENT_SECRET")
    token_url = "https://api.fitbit.com/oauth2/token"
    
    payload = {
        'client_id': client_id,
        'grant_type': 'authorization_code',
        'code': code,
        'code_verifier': code_verifier,
        'redirect_uri': os.getenv("FITBIT_REDIRECT_URI")
    }
    
    # Make the token request
    response = requests.post(token_url, data=payload, headers={
        'Authorization': 'Basic ' + base64.b64encode(f"{client_id}:{client_secret}".encode()).decode(),
        'Content-Type': 'application/x-www-form-urlencoded'
    })
    
    # Handle the response
    if response.status_code == 200:
        # Save the tokens
        tokens = response.json()
        with open(TOKEN_FILE_PATH, "w") as file:
            json.dump(tokens, file)
        
        print("Successfully connected to Fitbit")
        return redirect("http://localhost:3001/patient-dashboard")
    else:
        print("Failed to connect to Fitbit", response.json(), response.status_code)
        return jsonify({"error": "Failed to connect to Fitbit"}), 400
    

def get_fitbit_data(tries=1):
    with open(TOKEN_FILE_PATH, "r") as file:
        tokens = json.load(file)

    print("Fetching Fitbit data...")
    patient = Patient.query.filter_by(email=os.getenv('fitbit_user')).first()
    access_token = tokens['access_token']
    url_list = ["https://api.fitbit.com/1/user/-/activities/heart/date/today/1d/5min.json", "https://api.fitbit.com/1/user/-/activities/steps/date/today/1d.json", "https://api.fitbit.com/1/user/-/profile.json"]
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
                    responses.append((jsonify({"message": "Data fetched successfully"}), 200))
                except:
                    responses.append((jsonify({"error": "Data not present"}), 290))
            elif 'steps' in url:
                print('here')
                try:
                    steps = data['activities-steps'][0]['value']
                    # Store in daily steps
                    responses.append((jsonify({"message": "Data fetched successfully"}), 200))
                except:
                    responses.append(( jsonify({"error": "Data not present"}), 290))
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
            return jsonify({"error": "Failed to fetch data from Fitbit"}), 500
    return response

# In refresh_fitbit_tokens function
def refresh_fitbit_tokens(client_id, client_secret, refresh_token):
    print("Attempting to refresh tokens...")
    try:
        response = requests.post(
            "https://api.fitbit.com/oauth2/token",
            headers={
                "Authorization": "Basic " + base64.b64encode(
                    f"{client_id}:{client_secret}".encode()
                ).decode(),
                "Content-Type": "application/x-www-form-urlencoded"
            },
            data={
                "grant_type": "refresh_token",
                "refresh_token": refresh_token
            }
        )
        
        if response.status_code != 200:
            print(f"Fitbit token refresh failed: {response.status_code} - {response.text}")
            return None, None
            
        tokens = response.json()
        with open(TOKEN_FILE_PATH, "w") as file:
            json.dump(tokens, file)
            
        print("Fitbit token refresh successful!")
        return tokens.get("access_token"), tokens.get("refresh_token")
        
    except Exception as e:
        print(f"Token refresh error: {str(e)}")
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

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5001)
