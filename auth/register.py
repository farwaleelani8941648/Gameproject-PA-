from .user_model import register_user

def register_screen():
    print("=== Register ===")
    while True:
        username = input("Enter username: ").strip()
        if not username:
            print("Username cannot be empty.")
            continue
        email = input("Enter email: ").strip()
        if not email or '@' not in email:
            print("Please enter a valid email.")
            continue
        password = input("Enter password: ").strip()
        if not password:
            print("Password cannot be empty.")
            continue

        success, message = register_user(username, email, password)
        print(message)
        return success
