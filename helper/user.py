from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.hashers import make_password
from authentication.models import User
from .response import create_response

def create_user(user_data):
    """
    Create a new user after checking if the email already exists.
    """
    if User.objects.filter(email=user_data['email']).exists():
        return {"error": "User already exists"}, 409

    user = User.objects.create(
        fullname=user_data['fullname'],
        email=user_data['email'],
        password=user_data['password']  # Store hashed password
    )
    return {
        "id": user.id,
        "fullname": user.fullname,
        "email": user.email,
    }, 201


def get_all_users():
    """
    Get all users from the database.
    """
    users = User.objects.all().values("id", "fullname", "email", "user_type")
    return create_response(list(users), status=200)


def get_user_by_id(user_id):
    """
    Get a user by ID.
    """
    try:
        user = User.objects.get(id=user_id)
        return create_response({
            "id": user.id,
            "fullname": user.fullname,
            "email": user.email,
            "user_type": user.user_type
        }, status=200)
    except ObjectDoesNotExist:
        return create_response({"error": "User not found"}, status=404)


def delete_user_by_id(user_id):
    """
    Delete a user by ID.
    """
    try:
        user = User.objects.get(id=user_id)
        user.delete()
        return create_response({"message": "User deleted successfully"}, status=200)
    except ObjectDoesNotExist:
        return create_response({"error": "User not found"}, status=404)


def update_user_by_id(user_id, user_data):
    """
    Update user details by ID.
    """
    try:
        user = User.objects.get(id=user_id)
        
        if 'fullname' in user_data:
            user.fullname = user_data['fullname']
        
        if 'email' in user_data:
            user.email = user_data['email']
        
        if 'password' in user_data:
            user.password = user_data['password']  # Password should already be hashed
        
        user.save()

        return create_response({
            "id": user.id,
            "fullname": user.fullname,
            "email": user.email,
            "user_type": user.user_type
        }, status=200)

    except ObjectDoesNotExist:
        return create_response({"error": "User not found"}, status=404)
