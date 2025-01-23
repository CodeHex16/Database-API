from flask import Blueprint, jsonify, request
from app.services.user_services import (
    create_user, 
    get_all_users, 
    get_user_by_id, 
    update_user, 
    delete_user
)

user_bp = Blueprint('users', __name__)

# Create a user
@user_bp.route('/', methods=['POST'])
def create_user_route():
    try:
        data = request.get_json()
        if not data or not data.get('username') or not data.get('email') or not data.get('password'):
            return jsonify({"error": "Missing data"}), 400

        user = create_user(data)
        return jsonify({"id": user.id, "username": user.username, "email": user.email}), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

# Retrieve all users
@user_bp.route('/', methods=['GET'])
def get_users_route():
    users = get_all_users()
    return jsonify([{"id": user.id, "username": user.username, "email": user.email} for user in users])

# Retrieve a user by ID
@user_bp.route('/<int:user_id>', methods=['GET'])
def get_user_route(user_id):
    user = get_user_by_id(user_id)
    if user:
        return jsonify({"id": user.id, "username": user.username, "email": user.email})
    return jsonify({"error": "User not found"}), 404

# Update a user
@user_bp.route('/<int:user_id>', methods=['PUT'])
def update_user_route(user_id):
    data = request.get_json()
    user = update_user(user_id, data)
    if user:
        return jsonify({"id": user.id, "username": user.username, "email": user.email})
    return jsonify({"error": "User not found"}), 404

# Delete a user
@user_bp.route('/<int:user_id>', methods=['DELETE'])
def delete_user_route(user_id):
    success = delete_user(user_id)
    if success:
        return jsonify({"message": "User deleted"}), 200
    return jsonify({"error": "User not found"}), 404
