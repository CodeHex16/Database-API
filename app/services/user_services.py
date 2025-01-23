from app.models.user_model import User
from app.extensions import db
from werkzeug.security import generate_password_hash, check_password_hash

def create_user(data):
    """
    Create a user and save it to the database.
    """
    if User.query.filter_by(username=data['username']).first():
        raise ValueError("Username already exists")
    if User.query.filter_by(email=data['email']).first():
        raise ValueError("Email already exists")
    
    hashed_password = generate_password_hash(data['password'])
    user = User(username=data['username'], email=data['email'], password=hashed_password)
    db.session.add(user)
    db.session.commit()
    return user

def get_all_users():
    """
    Retrieve all users.
    """
    return User.query.all()

def get_user_by_id(user_id):
    """
    Retrieve a user by their ID.
    """
    return db.session.get(User, user_id)

def update_user(user_id, data):
    """
    Update user details.
    """
    user = db.session.get(User, user_id)
    if not user:
        return None

    user.username = data.get('username', user.username)
    user.email = data.get('email', user.email)
    if data.get('password'):
        user.password = generate_password_hash(data['password'])
    db.session.commit()
    return user

def delete_user(user_id):
    """
    Delete a user by their ID.
    """
    user = db.session.get(User, user_id)
    if user:
        db.session.delete(user)
        db.session.commit()
        return True
    return False
