from ninja import Router
from django.http import JsonResponse
from home.user_schema import UserRequest, UserResponse
from helper.user import create_user
from django.contrib.auth.hashers import make_password
from typing import List
from helper.user import get_all_users, get_user_by_id, delete_user_by_id, update_user_by_id
from home.user_schema import UpdateUserRequest


user_system = Router(tags=["User Management"])

@user_system.post('register/', response={200: UserResponse, 400: dict}, summary="Register User")
def register_user(request, user: UserRequest):
    """
    Endpoint for registering a new user.
    - Hash the password before storing it.
    """
    # Convert the Pydantic model into a dictionary
    user_data = user.dict()
    user_data['password'] = make_password(user_data['password'])  # Hash the password

    result = create_user(user_data)
    
    if isinstance(result, dict) and result.get("error"):  # Error occurred (e.g., user already exists)
        return JsonResponse(result, status=400, safe=False)  # Return error with 400 status

    # On successful user creation
    return JsonResponse(result, status=201, safe=False)  # Return the created user with 201 status



@user_system.get('users/', response=List[UserResponse], summary="Get All Users")
def get_all_users_view(request):
    """
    Fetch all users from the database.
    """
    users = get_all_users()
    return users


@user_system.get('user/{user_id}/', response=UserResponse, summary="Get User")
def get_user_view(request, user_id: int):
    """
    Get a user by ID.
    """
    result, status = get_user_by_id(user_id)
    return result, status


@user_system.delete('user/{user_id}/', summary="Delete User")
def delete_user_view(request, user_id: int):
    """
    Delete a user by ID.
    """
    result, status = delete_user_by_id(user_id)
    return result, status


@user_system.put('user/{user_id}/', response=UserResponse, summary="Update User")
def update_user_view(request, user_id: int, user: UpdateUserRequest):
    """
    Update user details by ID.
    Only provided fields will be updated.
    """
    user_data = user.dict(exclude_unset=True)  # Only include fields that were provided
    if user_data.get('password'):
        user_data['password'] = make_password(user_data['password'])  # Hash the new password if provided

    result, status = update_user_by_id(user_id, user_data)
    return result, status
