from payment import db

def create_database():
    print("Creating database tables...")
    try:
        db.create_all()
        print("Database tables created successfully!")
    except Exception as e:
        print(f"Error creating database: {str(e)}")

if __name__ == "__main__":
    create_database()
