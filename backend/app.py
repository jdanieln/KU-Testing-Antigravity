import os
import functools
from flask import Flask, jsonify, request, g

import firebase_admin
from firebase_admin import credentials, firestore, auth, storage
from dotenv import load_dotenv

# Load environment variables from the project root
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(dotenv_path)

app = Flask(__name__)
# Manual CORS Handling since flask-cors is hanging on OPTIONS
@app.after_request
def add_cors_headers(response):
    origin = request.headers.get('Origin')
    if origin in ["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:5174"]:
        response.headers['Access-Control-Allow-Origin'] = origin
        response.headers['Access-Control-Allow-Credentials'] = 'true'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, Access-Control-Allow-Credentials'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
    return response

@app.route('/api/<path:path>', methods=['OPTIONS'])
def handle_options(path):
    return jsonify({}), 200

# Initialize Firebase Admin SDK
cred_path = os.getenv('FIREBASE_CREDENTIALS', 'serviceAccountKey.json')

if not firebase_admin._apps:
    if os.getenv('FIREBASE_PRIVATE_KEY'):
        # Fix actual literal '\n' sequences from dotenv string
        private_key = os.getenv('FIREBASE_PRIVATE_KEY').replace('\\n', '\n')
        
        cred_dict = {
            "type": os.getenv('FIREBASE_TYPE', 'service_account'),
            "project_id": os.getenv('FIREBASE_PROJECT_ID'),
            "private_key_id": os.getenv('FIREBASE_PRIVATE_KEY_ID'),
            "private_key": private_key,
            "client_email": os.getenv('FIREBASE_CLIENT_EMAIL'),
            "client_id": os.getenv('FIREBASE_CLIENT_ID'),
            "auth_uri": os.getenv('FIREBASE_AUTH_URI', 'https://accounts.google.com/o/oauth2/auth'),
            "token_uri": os.getenv('FIREBASE_TOKEN_URI', 'https://oauth2.googleapis.com/token'),
            "auth_provider_x509_cert_url": os.getenv('FIREBASE_AUTH_PROVIDER_X509_CERT_URL', 'https://www.googleapis.com/oauth2/v1/certs'),
            "client_x509_cert_url": os.getenv('FIREBASE_CLIENT_X509_CERT_URL'),
            "universe_domain": os.getenv('FIREBASE_UNIVERSE_DOMAIN', 'googleapis.com')
        }
        cred = credentials.Certificate(cred_dict)
        firebase_admin.initialize_app(cred, {
            'storageBucket': os.getenv('FIREBASE_STORAGE_BUCKET', 'your-project-id.appspot.com')
        })
        print("Firebase Admin Initialized from environment variables")
        db = firestore.client()
    elif os.path.exists(cred_path):
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred, {
            'storageBucket': os.getenv('FIREBASE_STORAGE_BUCKET', 'your-project-id.appspot.com')
        })
        print(f"Firebase Admin Initialized from file: {cred_path}")
        db = firestore.client()
    else:
        print(f"Warning: Firebase credentials not found at {cred_path} or in env vars. Firebase features will not work.")
        db = None

# --- Middleware ---





def verify_token(f):
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        print("DEBUG: verify_token decorator called")
        
        # Preflight OPTIONS requests don't have the Authorization header
        # Let Flask-CORS handle them or return 200 OK
        if request.method == 'OPTIONS':
            return jsonify({}), 200

        if not db:
             # If DB not connected, mock auth for development ONLY if needed, or fail.
             # Failing is safer.
             return jsonify({'error': 'Database not connected'}), 503

        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            print("DEBUG: verify_token - Missing or invalid Authorization header")
            return jsonify({'error': 'Unauthorized', 'message': 'Missing Token'}), 401
        
        token = auth_header.split(' ')[1]
        try:
            # Verify Firebase ID Token
            decoded_token = auth.verify_id_token(token)
            uid = decoded_token['uid']
            
            # Fetch user from Firestore to get Role
            user_ref = db.collection('users').document(uid)
            user_doc = user_ref.get()
            
            if user_doc.exists:
                g.user = user_doc.to_dict()
                g.user['uid'] = uid
                print(f"DEBUG: verify_token - User found in Firestore. Role: {g.user.get('role')}")
                # Fallback: check if doc exists by email (Admin created user but with different Auth UID)
                req_json = request.get_json(silent=True) or {}
                email_to_check = req_json.get('email')
                if email_to_check:
                    users_by_email = db.collection('users').where('email', '==', email_to_check).limit(1).get()
                    if users_by_email:
                        matched_doc = users_by_email[0]
                        g.user = matched_doc.to_dict()
                        g.user['uid'] = uid # Keep the token's UID
                        g.user['original_uid'] = matched_doc.id # Keep a reference to merge later
                        print(f"DEBUG: verify_token - User found by EMAIL. Role: {g.user.get('role')}")
                    else:
                        print(f"DEBUG: verify_token - User {uid} NOT found in Firestore.")
                        g.user = {'uid': uid, 'role': 'GUEST'}
                else:
                    print(f"DEBUG: verify_token - User {uid} NOT found in Firestore.")
                    g.user = {'uid': uid, 'role': 'GUEST'}
                
            return f(*args, **kwargs)
        except Exception as e:
            print(f"Token verification error: {e}")
            return jsonify({'error': 'Unauthorized', 'message': 'Invalid Token'}), 401
            
    return decorated_function

def role_required(allowed_roles):
    def decorator(f):
        @functools.wraps(f)
        def decorated_function(*args, **kwargs):
            user_role = g.user.get('role')
            if user_role not in allowed_roles:
                 print(f"DEBUG: role_required - Access denied. User role: {user_role}, Allowed: {allowed_roles}")
                 return jsonify({'error': 'Forbidden', 'message': 'Insufficient Permissions'}), 403
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# --- Endpoints ---

@app.route('/api/auth/sync', methods=['POST', 'OPTIONS'])
@verify_token
def sync_user():
    """
    Called by frontend on login. Ensures user exists in Firestore.
    If new, sets default role 'PATIENT'.
    Returns the user's role.
    """
    uid = g.user['uid']
    user_data = g.user
    
    print(f"DEBUG: sync_user called for UID: {uid}")
    
    # Check if user actually exists in DB (verify_token might populate g.user as GUEST if not found)
    user_ref = db.collection('users').document(uid)
    doc = user_ref.get()
    
    if not doc.exists:
        req_json = request.get_json(silent=True) or {}
        email = req_json.get('email', '')
        
        # Check if the admin previously created a user with this email
        existing_users = db.collection('users').where('email', '==', email).limit(1).get()
        
        if existing_users:
            print(f"DEBUG: sync_user - Found existing user by email. Migrating old record to new Google UID {uid}")
            old_doc = existing_users[0]
            old_data = old_doc.to_dict()
            
            # Transfer old data to new UID doc
            user_ref.set(old_data)
            
            # Clean up old orphaned record created by Admin
            old_doc.reference.delete()
            
            # Need to update diagnoses that pointed to old UID
            try:
                 old_uid = old_doc.id
                 diagnoses_ref = db.collection('diagnoses').where('patientId', '==', old_uid).stream()
                 for d in diagnoses_ref:
                      d.reference.update({'patientId': uid})
                 print(f"DEBUG: Migrated diagnoses to new UID {uid}")
            except Exception as e:
                 print(f"Error migrating diagnoses: {e}")
                 
            return jsonify({'message': 'User synced and migrated', 'role': old_data.get('role')})
            
        else:
            # Create completely new user
            print(f"DEBUG: sync_user - Creating new user for {uid}")
            new_user = {
                'email': email,
                'displayName': req_json.get('displayName', ''),
                'role': 'PATIENT', # Default role
                'createdAt': firestore.SERVER_TIMESTAMP
            }
            user_ref.set(new_user)
            return jsonify({'message': 'User created', 'role': 'PATIENT'})
    else:
        current_role = user_data.get('role')
        if current_role == 'GUEST' and 'original_uid' in user_data:
             # Just in case fallback didn't catch properly in verify
             current_role = user_data.get('role', 'PATIENT')
             
        print(f"DEBUG: sync_user - User exists. Returning role: {current_role}")
        return jsonify({'message': 'User synced', 'role': current_role})

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        "status": "healthy",
        "firebase_connected": db is not None
    })

# Example protected route
@app.route('/api/admin/dashboard', methods=['GET'])
@verify_token
@role_required(['SUPER_ADMIN'])
def admin_dashboard():
    return jsonify({'message': 'Welcome Super Admin', 'data': 'Secret Data'})

@app.route('/api/admin/users', methods=['GET'])
@verify_token
@role_required(['SUPER_ADMIN'])
def list_users():
    """List all users for management."""
    users_ref = db.collection('users')
    docs = users_ref.stream()
    
    users = []
    for doc in docs:
        user = doc.to_dict()
        user['uid'] = doc.id
        users.append(user)
        
    return jsonify(users)

@app.route('/api/admin/users', methods=['POST'])
@verify_token
@role_required(['SUPER_ADMIN'])
def create_user():
    """Create a new user in Firebase Auth and Firestore."""
    data = request.json
    email = data.get('email')
    display_name = data.get('displayName', '')
    role = data.get('role', 'PATIENT')
    
    ALLOWED_ROLES = ['SUPER_ADMIN', 'DOCTOR', 'ASSISTANT', 'PATIENT']
    if role not in ALLOWED_ROLES:
        return jsonify({'error': 'Invalid role', 'allowed': ALLOWED_ROLES}), 400

    if not email:
        return jsonify({'error': 'Email is required'}), 400

    try:
        # Create user in Firebase Auth (No password required; allows linking by email later)
        user_record = auth.create_user(
            email=email,
            display_name=display_name
        )
        
        # Save user role in Firestore
        db.collection('users').document(user_record.uid).set({
            'email': email,
            'displayName': display_name,
            'role': role,
            'createdAt': firestore.SERVER_TIMESTAMP
        })
        
        return jsonify({'message': f'User created successfully', 'uid': user_record.uid}), 201

    except Exception as e:
        print(f"Error creating user: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/users/<uid>', methods=['PUT'])
@verify_token
@role_required(['SUPER_ADMIN'])
def update_user(uid):
    """Update a user's role and/or display name."""
    data = request.json
    new_role = data.get('role')
    new_display_name = data.get('displayName')
    
    ALLOWED_ROLES = ['SUPER_ADMIN', 'DOCTOR', 'ASSISTANT', 'PATIENT']
    
    user_ref = db.collection('users').document(uid)
    if not user_ref.get().exists:
        return jsonify({'error': 'User not found in Firestore'}), 404
        
    update_data = {}
    if new_role:
        if new_role not in ALLOWED_ROLES:
            return jsonify({'error': 'Invalid role', 'allowed': ALLOWED_ROLES}), 400
        update_data['role'] = new_role
        
    if new_display_name is not None:
        update_data['displayName'] = new_display_name
        try:
             auth.update_user(uid, display_name=new_display_name)
        except Exception as e:
             print(f"Error updating display name in auth: {e}")
             return jsonify({'error': str(e)}), 500

    if update_data:
        user_ref.update(update_data)
        
    return jsonify({'message': f'User updated successfully'})

@app.route('/api/admin/users/<uid>', methods=['DELETE'])
@verify_token
@role_required(['SUPER_ADMIN'])
def delete_user(uid):
    """Delete a user from Firebase Auth and Firestore."""
    try:
        # Delete from Firebase Auth
        auth.delete_user(uid)
        
        # Delete from Firestore
        db.collection('users').document(uid).delete()
        
        return jsonify({'message': 'User deleted successfully'})
    except Exception as e:
        print(f"Error deleting user: {e}")
        return jsonify({'error': str(e)}), 500

# --- Medical Diagnoses Endpoints ---

@app.route('/api/diagnoses', methods=['POST'])
@verify_token
@role_required(['SUPER_ADMIN', 'DOCTOR'])
def create_diagnosis():
    """Create a new medical diagnosis for a patient."""
    data = request.json
    patient_uid = data.get('patientId')
    symptoms = data.get('symptoms')
    diagnosis_text = data.get('diagnosis')
    prescription = data.get('prescription')
    
    if not all([patient_uid, symptoms, diagnosis_text]):
        return jsonify({'error': 'Missing required fields (patientId, symptoms, diagnosis)'}), 400
        
    try:
        # Verify the patient actually exists
        patient_ref = db.collection('users').document(patient_uid)
        patient_doc = patient_ref.get()
        if not patient_doc.exists:
             return jsonify({'error': 'Patient not found'}), 404
             
        # Add to the new "diagnoses" collection
        new_diagnosis = {
            'patientId': patient_uid,
            'doctorId': g.user['uid'],
            'doctorName': g.user.get('displayName', 'Unknown Doctor'),
            'symptoms': symptoms,
            'diagnosis': diagnosis_text,
            'prescription': prescription or '',
            'createdAt': firestore.SERVER_TIMESTAMP
        }
        
        _, doc_ref = db.collection('diagnoses').add(new_diagnosis)
        return jsonify({'message': 'Diagnosis created successfully', 'id': doc_ref.id}), 201
        
    except Exception as e:
        print(f"Error creating diagnosis: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/diagnoses/patient/<patient_uid>', methods=['GET'])
@verify_token
def get_patient_diagnoses(patient_uid):
    """Get all diagnoses for a specific patient.
    Accessible by:
    - The actual patient
    - Any DOCTOR
    - Any SUPER_ADMIN
    """
    user_role = g.user.get('role')
    user_uid = g.user['uid']
    
    # Check permissions logic
    if user_role == 'PATIENT' and user_uid != patient_uid:
        return jsonify({'error': 'Forbidden', 'message': 'You can only view your own history.'}), 403
        
    if user_role not in ['SUPER_ADMIN', 'DOCTOR', 'PATIENT']:
         return jsonify({'error': 'Forbidden', 'message': 'Insufficient Permissions'}), 403

    try:
        diagnoses_ref = db.collection('diagnoses').where('patientId', '==', patient_uid).order_by('createdAt', direction=firestore.Query.DESCENDING)
        docs = diagnoses_ref.stream()
        
        diagnoses = []
        for doc in docs:
            item = doc.to_dict()
            item['id'] = doc.id
            diagnoses.append(item)
            
        return jsonify(diagnoses), 200
        
    except Exception as e:
        print(f"Error retrieving diagnoses: {e}")
        return jsonify({'error': str(e)}), 500
        
@app.route('/api/doctors/patients', methods=['GET'])
@verify_token
@role_required(['SUPER_ADMIN', 'DOCTOR', 'ASSISTANT'])
def list_patients():
    """Returns a list of all users with PATIENT role."""
    try:
        users_ref = db.collection('users').where('role', '==', 'PATIENT')
        docs = users_ref.stream()
        
        patients = []
        for doc in docs:
            user = doc.to_dict()
            user['uid'] = doc.id
            patients.append(user)
            
        return jsonify(patients), 200
    except Exception as e:
         print(f"Error listing patients: {e}")
         return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    port = int(os.getenv('API_PORT', 5005))
    app.run(debug=False, port=port)
