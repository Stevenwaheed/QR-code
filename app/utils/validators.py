import random
import re
from werkzeug.security import generate_password_hash



def set_password(password):
    password_hash = generate_password_hash(password)
    return password_hash


def is_valid_email(email):
    # Regular expression for validating an Email
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    # Match the pattern against the provided email
    if re.match(pattern, email):
        return True
    else:
        return False
    
    
    
def is_valid_phone_number(phone):
    # Regular expression for validating a phone number
    # This pattern matches various formats like (123) 456-7890, 123-456-7890, 1234567890, +31612345678, etc.
    pattern = r'^\+?[\d\s().-]{7,15}$'
    
    # Match the pattern against the provided phone number
    if re.match(pattern, phone):
        return True
    else:
        return False
    
    

def generate_otp(length=6):
    """Generate a numeric OTP of specified length."""
    return ''.join(random.choices('0123456789', k=length))

    
    
def validate_password(password):
    """
    Validate password strength.
    - Minimum 8 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one number
    - At least one special character
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    
    if not re.search(r'\d', password):
        return False, "Password must contain at least one number"
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False, "Password must contain at least one special character"
    
    return True, "Password is valid"
