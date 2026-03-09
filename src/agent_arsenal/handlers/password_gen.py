"""Password generator handler."""
import secrets
import string


def generate_password(
    length: int = 16,
    use_special: bool = True,
    use_digits: bool = True,
    use_uppercase: bool = True,
) -> str:
    """Generate a secure random password.

    Args:
        length: Password length (8-128)
        use_special: Include special characters
        use_digits: Include digits
        use_uppercase: Include uppercase letters

    Returns:
        Generated password or error message
    """
    if length < 8 or length > 128:
        return "Error: Password length must be between 8 and 128"

    # Build character pool
    chars = string.ascii_lowercase  # Always include lowercase
    if use_uppercase:
        chars += string.ascii_uppercase
    if use_digits:
        chars += string.digits
    if use_special:
        chars += "!@#$%^&*"

    if not chars:
        return "Error: At least one character type must be enabled"

    # Generate password ensuring at least one of each type
    password = []
    required = [string.ascii_lowercase]
    if use_uppercase:
        required.append(string.ascii_uppercase)
    if use_digits:
        required.append(string.digits)
    if use_special:
        required.append("!@#$%^&*")

    # Add one of each required character type
    for char_set in required:
        password.append(secrets.choice(char_set))

    # Fill remaining length with random characters
    remaining = length - len(password)
    password.extend(secrets.choice(chars) for _ in range(remaining))

    # Shuffle to avoid predictable positions
    password_list = list(password)
    for i in range(len(password_list) - 1, 0, -1):
        j = secrets.randbelow(i + 1)
        password_list[i], password_list[j] = password_list[j], password_list[i]

    return "".join(password_list)
