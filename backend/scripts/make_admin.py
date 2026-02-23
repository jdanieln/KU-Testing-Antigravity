import os
import sys
import firebase_admin
from firebase_admin import credentials, firestore, auth
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
    
    # Query users by email in Firestore
    users_ref = db.collection('users')
    query = users_ref.where('email', '==', email).limit(1).stream()
    
    user_doc = None
    for doc in query:
        user_doc = doc
        break
    
    if user_doc:
        print(f"Found user in Firestore: {user_doc.id} ({email})")
        users_ref.document(user_doc.id).update({'role': 'SUPER_ADMIN'})
        print(f"Success! {email} is now a SUPER_ADMIN.")
    else:
        print(f"User {email} not found in Firestore. Checking Firebase Auth...")
        try:
            # Try to find user in Firebase Auth
            user_record = auth.get_user_by_email(email)
            uid = user_record.uid
            print(f"Found user in Firebase Auth: {uid}")
            
            # Create user in Firestore
            new_user = {
                'email': email,
                'role': 'SUPER_ADMIN',
                'createdAt': firestore.SERVER_TIMESTAMP,
                'displayName': user_record.display_name or ''
            }
            users_ref.document(uid).set(new_user)
            print(f"Success! Created user {email} in Firestore as SUPER_ADMIN.")
            
        except auth.UserNotFoundError:
            print(f"Error: User with email {email} not found in Auth or Firestore.")
            print("Please sign up first to create the account.")
        except Exception as e:
            print(f"An error occurred: {e}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python make_admin.py <email>")
    else:
        make_admin(sys.argv[1])
