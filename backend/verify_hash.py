
from app.auth.security import verify_password, get_password_hash
import sys

try:
    print("Testing password hashing...")
    pwd = "secretpassword"
    hashed = get_password_hash(pwd)
    print(f"Hash: {hashed}")
    
    print("Testing password verification...")
    is_valid = verify_password(pwd, hashed)
    print(f"Verification result: {is_valid}")
    
    if not is_valid:
        raise Exception("Verification failed!")
        
    print("Hashing works correctly.")
    
except Exception as e:
    print(f"Hashing FAILED: {e}")
    import traceback
    traceback.print_exc()
