import os
import sys
import firebase_admin
from firebase_admin import credentials, firestore
from dotenv import load_dotenv

# Add backend directory to sys.path to load env correctly if needed
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

def make_admin(email):
    # Initialize Firebase
    # specific path logic to find serviceAccountKey.json relatively to this script
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # Expecting key in backend/ (parent of scripts/)
    cred_path = os.path.join(current_dir, '..', 'serviceAccountKey.json')
    
    # Fallback env var if set (absolute path preferred if used)
    env_path = os.getenv('FIREBASE_CREDENTIALS')
    if env_path:
        cred_path = env_path

    if not os.path.exists(cred_path):
        print(f"Error: Credentials file not found at {cred_path}")
        print("Please ensure 'serviceAccountKey.json' is in the 'backend/' directory.")
        return

    cred = credentials.Certificate(cred_path)
    if not firebase_admin._apps:
        firebase_admin.initialize_app(cred)
    
    db = firestore.client()
    
    # Query users by email
    users_ref = db.collection('users')
    query = users_ref.where('email', '==', email).limit(1).stream()
    
    user_doc = None
    for doc in query:
        user_doc = doc
        break
    
    if user_doc:
        print(f"Found user: {user_doc.id} ({email})")
        users_ref.document(user_doc.id).update({'role': 'SUPER_ADMIN'})
        print(f"Success! {email} is now a SUPER_ADMIN.")
    else:
        print(f"Error: User with email {email} not found. Please log in first to create the account.")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python make_admin.py <email>")
    else:
        make_admin(sys.argv[1])
