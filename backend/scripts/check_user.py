import os
import sys
import firebase_admin
from firebase_admin import credentials, firestore
from dotenv import load_dotenv

# Add backend directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

def check_user(email):
    # Initialize Firebase
    current_dir = os.path.dirname(os.path.abspath(__file__))
    cred_path = os.path.join(current_dir, '..', 'serviceAccountKey.json')
    
    env_path = os.getenv('FIREBASE_CREDENTIALS')
    if env_path:
        cred_path = env_path

    if not os.path.exists(cred_path):
        print(f"Error: Credentials file not found at {cred_path}")
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
        print(f"User Found: {user_doc.id}")
        print(f"Data: {user_doc.to_dict()}")
    else:
        print(f"User with email {email} NOT found in Firestore.")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python check_user.py <email>")
    else:
        check_user(sys.argv[1])
