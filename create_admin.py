"""
Script to create an admin user for STAT GLOBAL e-commerce platform.
You can either create a new admin account or promote an existing user.
"""

from website import create_app, db
from website.models import User
from werkzeug.security import generate_password_hash

def create_admin():
    app = create_app()
    
    with app.app_context():
        print("=" * 60)
        print("STAT GLOBAL - Admin Account Manager")
        print("=" * 60)
        print()
        print("Choose an option:")
        print("1. Create a NEW admin account")
        print("2. Promote an EXISTING user to admin")
        print()
        
        choice = input("Enter your choice (1 or 2): ").strip()
        print()
        
        if choice == "1":
            # Create a new admin account
            print("Creating a new admin account...")
            print("-" * 60)
            
            email = input("Email address: ").strip()
            
            # Check if email already exists
            existing_user = User.query.filter_by(email=email).first()
            if existing_user:
                print(f"\n✗ Error: Email '{email}' is already registered.")
                promote = input("Would you like to promote this user to admin instead? (y/n): ").strip().lower()
                if promote == 'y':
                    if existing_user.is_admin:
                        print(f"\nUser {email} is already an admin!")
                    else:
                        existing_user.is_admin = True
                        db.session.commit()
                        print(f"\n✓ Success! User {email} is now an admin.")
                return
            
            first_name = input("First name: ").strip()
            last_name = input("Last name: ").strip()
            password = input("Password (min 7 characters): ").strip()
            
            if len(password) < 7:
                print("\n✗ Error: Password must be at least 7 characters.")
                return
            
            # Create new admin user
            new_admin = User(
                email=email,
                first_name=first_name,
                last_name=last_name,
                password=generate_password_hash(password, method='pbkdf2:sha256'),
                is_admin=True
            )
            
            db.session.add(new_admin)
            db.session.commit()
            
            print()
            print("=" * 60)
            print("✓ SUCCESS! Admin account created!")
            print("=" * 60)
            print(f"Email: {email}")
            print(f"Name: {first_name} {last_name}")
            print(f"Admin Status: ✓ Active")
            print()
            print("You can now log in at: http://localhost:5000/login")
            print("Admin panel: http://localhost:5000/admin")
            print("=" * 60)
            
        elif choice == "2":
            # Promote existing user
            print("Promoting an existing user to admin...")
            print("-" * 60)
            print()
            print("Existing users in database:")
            users = User.query.all()
            
            if not users:
                print("  No users found. Please create an account first at /sign-up")
                return
            
            for i, u in enumerate(users, 1):
                admin_status = "✓ Admin" if u.is_admin else "Regular User"
                print(f"  {i}. {u.email} ({u.first_name} {u.last_name}) - {admin_status}")
            
            print()
            email = input("Enter the email address to promote: ").strip()
            
            user = User.query.filter_by(email=email).first()
            
            if user:
                if user.is_admin:
                    print(f"\nUser {user.email} is already an admin!")
                else:
                    user.is_admin = True
                    db.session.commit()
                    print()
                    print("=" * 60)
                    print("✓ SUCCESS! User promoted to admin!")
                    print("=" * 60)
                    print(f"Email: {user.email}")
                    print(f"Name: {user.first_name} {user.last_name}")
                    print(f"Admin Status: ✓ Active")
                    print()
                    print("Admin panel: http://localhost:5000/admin")
                    print("=" * 60)
            else:
                print(f"\n✗ Error: User with email '{email}' not found.")
                print("  Please check the email address and try again.")
        
        else:
            print("✗ Invalid choice. Please run the script again and choose 1 or 2.")

if __name__ == '__main__':
    create_admin()
