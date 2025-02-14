from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
import os
from flask_cors import CORS
from sqlalchemy.exc import SQLAlchemyError
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
CORS(app)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('postgres-setup-url') # Replace <user>, <password>, <database_name>
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY') # DONT FORGET ABOUT THE .env file that's gitignored

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
    avg_heartrate = db.Column(db.Integer)
    heart_score = db.Column(db.Integer, default=0)
    steps = db.Column(db.Integer)

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

    if not data.get('email') or not data.get('password'):
        return jsonify({"error": "Email and password are required"}), 400

    # Check both doctors and patients
    user = Doctor.query.filter_by(email=data['email']).first() or \
           Patient.query.filter_by(email=data['email']).first()

    if not user:
        return jsonify({"error": "User not found"}), 404

    if not bcrypt.check_password_hash(user.password, data['password']):
        return jsonify({"error": "Invalid password"}), 401

    # Simplified: just use email as identity
    access_token = create_access_token(identity=user.email)

    return jsonify({
        "message": "Login successful",
        "access_token": access_token,
        "user_type": "doctor" if isinstance(user, Doctor) else "patient",
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