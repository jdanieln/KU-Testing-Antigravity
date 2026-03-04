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
            else:
                # User authenticated with Google but not in our DB yet (First login sync pending)
                # Or could treat as "Guest"
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
        # Create new user
        print(f"DEBUG: sync_user - Creating new user for {uid}")
        new_user = {
            'email': request.json.get('email', ''), # Frontend should send this or we extract from token if possible
            'displayName': request.json.get('displayName', ''),
            'role': 'PATIENT', # Default role
            'createdAt': firestore.SERVER_TIMESTAMP
        }
        # In a real scenario, extracting email/name from decoded_token is safer if token passed details
        # For now, we trust the sync payload or token
        
        user_ref.set(new_user)
        return jsonify({'message': 'User created', 'role': 'PATIENT'})
    else:
        current_role = user_data.get('role')
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

@app.route('/api/admin/users/<uid>/role', methods=['PUT'])
@verify_token
@role_required(['SUPER_ADMIN'])
def update_user_role(uid):
    """Update a user's role."""
    new_role = request.json.get('role')
    ALLOWED_ROLES = ['SUPER_ADMIN', 'DOCTOR', 'ASSISTANT', 'PATIENT']
    
    if new_role not in ALLOWED_ROLES:
        return jsonify({'error': 'Invalid role', 'allowed': ALLOWED_ROLES}), 400
        
    user_ref = db.collection('users').document(uid)
    if not user_ref.get().exists:
        return jsonify({'error': 'User not found'}), 404
        
    user_ref.update({'role': new_role})
    return jsonify({'message': f'User role updated to {new_role}'})


if __name__ == '__main__':
    port = int(os.getenv('API_PORT', 5005))
    app.run(debug=False, port=port)
