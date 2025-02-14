from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
import os
from flask_cors import CORS
from sqlalchemy.exc import SQLAlchemyError


app = Flask(__name__)
CORS(app)
app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql://postgres:PostgresHuh@localhost:5432/postgres"# Replace <user>, <password>, <database_name>
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = 'your_secret_key' # os.getenv('FLASK_SECRET_KEY') # DONT FORGET ABOUT THE .env file that's gitignored

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
jwt = JWTManager(app)

# Models
class Patient(db.Model):
    __tablename__ = 'patient'

    u_id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.Text, nullable=False, unique=True)
    name = db.Column(db.Text, nullable=False)
    password = db.Column(db.Text, nullable=False)
    avg_heartrate = db.Column(db.Integer)
    heart_score = db.Column(db.Integer, default=0)
    steps = db.Column(db.Integer)

    friends = db.relationship(
        'Patient',
        secondary='friendship',
        primaryjoin='Patient.u_id == Friendship.patient_id',
        secondaryjoin='Patient.u_id == Friendship.friend_id',
        backref='friend_list',
        lazy='dynamic'
    )

class Friendship(db.Model):
    __tablename__ = 'friendship'

    patient_id = db.Column(db.Integer, db.ForeignKey('patient.u_id'), primary_key=True)
    friend_id = db.Column(db.Integer, db.ForeignKey('patient.u_id'), primary_key=True)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

# Routes

class Doctor(db.Model):
    __tablename__ = 'doctor'

    u_id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.Text, nullable=False, unique=True)
    name = db.Column(db.Text, nullable=False)
    password = db.Column(db.Text, nullable=False)
    specialty = db.Column(db.Text)
    # patients = db.relationship(
    #     'Patient',
    #     secondary='doctor_patient',
    #     backref=db.backref('doctors', lazy='dynamic'),
    #     lazy='dynamic'
    # )

# class DoctorPatient(db.Model):
#     __tablename__ = 'doctor_patient'
#     doctor_id = db.Column(db.Integer, db.ForeignKey('doctor.u_id'), primary_key=True)
#     patient_id = db.Column(db.Integer, db.ForeignKey('patient.u_id'), primary_key=True)
#     assigned_date = db.Column(db.DateTime, default=db.func.current_timestamp())

# Updated routes
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

    if not data.get('email') or not data.get('password'):
        return jsonify({"error": "Email and password are required"}), 400

    # Check both doctors and patients
    user = Doctor.query.filter_by(email=data['email']).first() or \
           Patient.query.filter_by(email=data['email']).first()

    if not user:
        return jsonify({"error": "User not found"}), 404

    if not bcrypt.check_password_hash(user.password, data['password']):
        return jsonify({"error": "Invalid password"}), 401

    # Create token with user type information
    user_type = 'doctor' if isinstance(user, Doctor) else 'patient'
    access_token = create_access_token(identity=user.email)

    return jsonify({
        "message": "Login successful",
        "access_token": access_token,
        "user_type": user_type,
        "u_id": user.u_id
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

# Friend Addition
@app.route('/add_friend', methods=['POST'])
@jwt_required()
def add_friend():
    data = request.get_json()

    u_id_1 = data.get('u_id_1')
    u_id_2 = data.get('u_id_2')

    if (not u_id_1) or (not u_id_2):
        return jsonify({"error": "Both u_id_1 and u_id_2 must be provided"}), 400

    if u_id_1 == u_id_2:
        return jsonify({"error": "You cannot be friends with yourself"}), 400

    patient_1 = Patient.query.get(u_id_1)
    patient_2 = Patient.query.get(u_id_2)

    if (not patient_1) or (not patient_2):
        return jsonify({"error": "One or both patients do not exist"}), 404

    existing_friendship = Friendship.query.filter_by(patient_id=u_id_1, friend_id=u_id_2).first()
    if existing_friendship:
        return jsonify({"error": "Friendship already exists"}), 400

    friendship1 = Friendship(patient_id=u_id_1, friend_id=u_id_2)
    friendship2 = Friendship(patient_id=u_id_2, friend_id=u_id_1)

    db.session.add(friendship1)
    db.session.add(friendship2)
    db.session.commit()

    return jsonify({"message": "Friend added successfully"}), 201

# Friend List
@app.route('/list_friends/<int:user_id>', methods=['GET'])
@jwt_required()
def list_friends(user_id):
    patient = Patient.query.get(user_id)

    if not patient:
        return jsonify({"error": "Patient not found"}), 404

    friends = [{"u_id": friend.u_id, "name": friend.name} for friend in patient.friends]

    return jsonify({"friends": friends}), 200

# Friend Removal
@app.route('/remove_friend', methods=['DELETE'])
@jwt_required()
def remove_friend():
    data = request.get_json()

    u_id_1 = data.get('u_id_1')
    u_id_2 = data.get('u_id_2')

    if (not u_id_1) or (not u_id_2):
        return jsonify({"error": "Both u_id_1 and u_id_2 are required"}), 400
    patient1 = Patient.query.get(u_id_1)
    patient2 = Patient.query.get(u_id_2)

    if (not patient1) or (not patient2):
        return jsonify({"error": "One or both patients not found"}), 404

    friendship1 = Friendship.query.filter_by(patient_id=u_id_1, friend_id=u_id_2).first()
    friendship2 = Friendship.query.filter_by(patient_id=u_id_2, friend_id=u_id_1).first()

    if (not friendship1) or (not friendship2):
        return jsonify({"error": "Friendship does not exist"}), 404

    db.session.delete(friendship1)
    db.session.delete(friendship2)
    db.session.commit()

    return jsonify({"message": "Friend removed successfully"}), 200


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
        db.session.commit()

        return jsonify({"message": "Test submitted successfully", "heart_score": heart_score}), 200

    except SQLAlchemyError as e:
        # Handle database errors
        db.session.rollback()  # Rollback any transaction to avoid inconsistent states
        return jsonify({"error": f"Database error: {str(e)}"}), 500

    except Exception as e:
        # Handle any other unforeseen errors
        return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500

@app.route('/get_patient', methods=['GET'])
@jwt_required()
def get_patient_data():
    # Get the email from the JWT token for verification
    user_email = get_jwt_identity()

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

# @app.route('/get_doctor', methods=['GET'])
# @jwt_required()
# def get_doctor_data():
#     # Get the identity from JWT token
#     user_identity = get_jwt_identity()

#     # Since we're storing dictionary in identity now, we need to get email from it
#     if isinstance(user_identity, dict):
#         user_email = user_identity.get('email')
#     else:
#         user_email = user_identity

#     # Verify this user is requesting their own data
#     doctor = Doctor.query.filter_by(email=str(user_email)).first()
#     if not doctor:
#         return jsonify({"error": "Doctor not found"}), 404

#     return jsonify({
#         "doctor": {
#             "name": doctor.name,
#             "specialty": doctor.specialty,
#             "email": doctor.email
#         }
#     }), 200

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5001)