import secrets
import string
from django.contrib.auth.hashers import make_password

def generate_unhashable_password(length=16):
    # Define character sets
    uppercase = string.ascii_uppercase
    lowercase = string.ascii_lowercase
    digits = string.digits
    symbols = "!@#$%^&*_+-=?"

    # Combine all characters
    all_chars = uppercase + lowercase + digits + symbols

    while True:
        password = []
        # Ensure at least one character from each set
        password.append(secrets.choice(uppercase))
        password.append(secrets.choice(lowercase))
        password.append(secrets.choice(digits))
        password.append(secrets.choice(symbols))
    
        # Fill remaining length with random choices
        password += [secrets.choice(all_chars) for _ in range(length - 4)]
    
        # Shuffle to avoid predictable patterns
        secrets.SystemRandom().shuffle(password)
    
        # Convert list to string
        final_password = ''.join(password)
    
        # Additional safety check (optional)
        if (sum(c.isupper() for c in final_password) >= 2 and
            sum(c.islower() for c in final_password) >= 2 and
            sum(c.isdigit() for c in final_password) >= 2 and
            sum(c in symbols for c in final_password) >= 2):
        
            return make_password(final_password)