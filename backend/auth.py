import bcrypt

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed password."""
    try:
        password_bytes = plain_password.encode('utf-8')
        hashed_bytes = hashed_password.encode('utf-8')
        return bcrypt.checkpw(password_bytes, hashed_bytes)
    except Exception as e:
        print(f"Error verifying password: {e}")
        return False

def get_password_hash(password: str) -> str:
    """Generate a bcrypt hash of the password."""
    # Generate a salt and hash the password
    salt = bcrypt.gensalt()
    password_bytes = password.encode('utf-8')
    hashed_password = bcrypt.hashpw(password_bytes, salt)
    # Return as a string for database storage
    return hashed_password.decode('utf-8')