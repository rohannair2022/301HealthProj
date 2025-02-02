from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://<user>:<password>@localhost/<database_name>' # CHANGE <user>, <password>, <datatbase_name> TO YOUR LOCAL POSGRESQL SERVER
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)



# Models
class Patient(db.Model):
    __tablename__ = 'patient'

    u_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, nullable=False)
    email = db.Column(db.Text, nullable=False)
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

# Patient Creation
@app.route('/create_patient', methods=['POST'])
def create_patient():
    data = request.get_json()

    if ('name' not in data) or ('password' not in data) or ('email' not in data):
        return jsonify({"error": "Missing required fields"}), 400

    new_patient = Patient(
        name=data['name'],
        password=data['password'],
        avg_heartrate=data.get('avg_heartrate', 0), 
        heart_score=data.get('heart_score', 0),      
        steps=data.get('steps', 0)                    
    )

    db.session.add(new_patient)
    db.session.commit()

    return jsonify({"message": "Patient created successfully", "u_id": new_patient.u_id}), 201

# Patient Deletion
@app.route('/remove_patient/<int:u_id>', methods=['DELETE'])
def remove_patient(u_id):
    patient = Patient.query.get(u_id)
    if not patient:
        return jsonify({"error": "Patient not found"}), 404

    # Deletes all the affected friendship(s)
    Friendship.query.filter(
        (Friendship.patient_id == u_id) | (Friendship.friend_id == u_id)
    ).delete()

    db.session.delete(patient)
    db.session.commit()

    return jsonify({"message": "Patient and related friendships removed successfully"}), 200

# Friend Addition
@app.route('/add_friend', methods=['POST'])
def add_friend():
    data = request.get_json()

    u_id_1 = data.get('u_id_1')
    u_id_2 = data.get('u_id_2')

    if (not u_id_1) or (not u_id_2):
        return jsonify({"error": "Both u_id_1 and u_id_2 must be provided"}), 400

    if u_id_1 == u_id_2:
        return jsonify({"error": "You cannot be friends with yourself"}), 400

    # Check for if both users exist
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

# Friend Listation
@app.route('/list_friends/<int:user_id>', methods=['GET'])
def list_friends(user_id):
    patient = Patient.query.get(user_id)

    if not patient:
        return jsonify({"error": "Patient not found"}), 404

    friends = [{"u_id": friend.u_id, "name": friend.name} for friend in patient.friends]

    return jsonify({"friends": friends}), 200

# Friend Removation
@app.route('/remove_friend', methods=['DELETE'])
def remove_friend():
    data = request.get_json()

    u_id_1 = data.get('u_id_1')
    u_id_2 = data.get('u_id_2')

    if (not u_id_1) or (not u_id_2):
        return jsonify({"error": "Both u_id_1 and u_id_2 are required"}), 400
    
    # Check for if both users exist 
    patient1 = Patient.query.get(u_id_1)
    patient2 = Patient.query.get(u_id_2)

    if (not patient1) or (not patient2):
        return jsonify({"error": "One or both patients not found"}), 404

    # Check for if both users are friended
    friendship1 = Friendship.query.filter_by(patient_id=u_id_1, friend_id=u_id_2).first()
    friendship2 = Friendship.query.filter_by(patient_id=u_id_2, friend_id=u_id_1).first()

    if (not friendship1) or (not friendship2):
        return jsonify({"error": "Friendship does not exist"}), 404

    db.session.delete(friendship1)
    db.session.delete(friendship2)
    db.session.commit()

    return jsonify({"message": "Friend removed successfully"}), 200



if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5001) # THIS IS THE PORT TO CONNECT TO (for API requests)
