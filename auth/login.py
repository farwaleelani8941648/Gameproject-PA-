from .user_model import login_user

def login_screen():
    print("=== Login ===")
    while True:
        username = input("Enter username: ").strip()
        if not username:
            print("Username cannot be empty.")
            continue
        password = input("Enter password: ").strip()
        if not password:
            print("Password cannot be empty.")
            continue

        success, result = login_user(username, password)
        if success:
            print(f"Welcome, {username}!")
            return result  # user tuple
        else:
            print(result)
            # Optionally: break or return None after one attempt, or loop for retry
            retry = input("Try again? (y/n): ").strip().lower()
            if retry != 'y':
                return None
