from ninja import Router
from django.http import JsonResponse
from home.user_schema import UserRequest, UserResponse, UserLoginRequest, UserLoginResponse
from helper.user import create_user
from django.contrib.auth.hashers import make_password
from typing import List
from helper.user import get_all_users, get_user_by_id, delete_user_by_id, update_user_by_id
from home.user_schema import UpdateUserRequest
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import ValidationError
import json
from authentication.models import User
from django.contrib.auth import authenticate
from django.utils import timezone
from wallet.models import Wallets
import uuid
from uuid import uuid4
from helper.utils import generate_user_wallet
import traceback


user_system = Router(tags=["User Management"])

@csrf_exempt
@user_system.post('register/', response=UserResponse, summary="Register User")
def register_user(request):
    if request.method != "POST":
        return JsonResponse({"error": "Only POST requests are allowed"}, status=405)

    try:
        body = json.loads(request.body)
        user_data = UserRequest(**body).dict()

        user = User.objects.create_user(
            email=user_data['email'],
            fullname=user_data['fullname'],
            password=user_data['password']
        )

        return JsonResponse(
            {
                "message": "User registered successfully",
                "user_id": str(user.id),
                "email": user.email,
                "fullname": user.fullname,
            },
            status=201,
        )
    except ValidationError as ve:
        return JsonResponse({"error": ve.errors()}, status=400)
    except ValueError as ve:
        return JsonResponse({"error": str(ve)}, status=400)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)



@csrf_exempt
@user_system.post('login/', response={200: UserLoginResponse, 400: dict, 401: dict, 500: dict}, summary="Login User")
def login_user(request):
    """
    Endpoint for logging in a user.
    """
    if request.method != "POST":
        return JsonResponse({"error": "Only POST requests are allowed"}, status=405)

    try:
        body = json.loads(request.body)  # Parse JSON body
        email = body.get('email')
        password = body.get('password')

        if not email or not password:
            return JsonResponse({"error": "Bad request: Missing credentials"}, status=400)

        # Query SQLite database
        user = User.objects.filter(email=email).first()
        if not user:
            return JsonResponse({"error": "User not found"}, status=401)

        # Verify password
        if not user.check_password(password):
            return JsonResponse({"error": "Invalid password"}, status=401)

        # Update last login
        user.last_login = timezone.now()
        user.save()

        # Prepare response data
        response_data = {
            "message": "Login successful",
            "user_id": str(user.id),
            "email": user.email,
            "fullname": user.fullname,
            "last_login": user.last_login.isoformat(),
        }

        return JsonResponse(response_data, status=200)

    except ValidationError as ve:
        return JsonResponse({"error": ve.errors()}, status=400)
    except ValueError as ve:
        return JsonResponse({"error": str(ve)}, status=400)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

@csrf_exempt
@user_system.post(
    "createpin/", 
    response={200: dict, 400: dict, 401: dict, 405: dict, 500: dict}, 
    summary="Create a wallet PIN for user"
)
def create_pin(request):
    """
    Create a 4-digit wallet PIN for the user using data from the request body.
    """
    if request.method != "POST":
        return JsonResponse({"error": "Only POST requests are allowed"}, status=405)

    try:
        # Parse request body
        data = json.loads(request.body.decode("utf-8"))
        user_id = data.get('userId')
        pin = data.get('pin')
        confirm_pin = data.get('confirmPin')  # Confirmation PIN

        # Validate required fields
        if not user_id or not pin or not confirm_pin:
            return JsonResponse({"error": "Missing required fields: userId, pin, and confirmPin"}, status=400)

        # Validate PIN format
        if not isinstance(pin, str) or not pin.isdigit() or len(pin) != 4:
            return JsonResponse({"error": "PIN must be exactly 4 digits"}, status=400)
        
        if pin != confirm_pin:
            return JsonResponse({"error": "PIN and confirmPin do not match"}, status=400)

        # Fetch user
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return JsonResponse({"error": "User not found"}, status=401)

        # Check if PIN already exists
        if user.wallet_pin:
            return JsonResponse({"error": "Wallet PIN already exists for this user"}, status=400)

        # Hash the PIN and save
        user.wallet_pin = make_password(pin)
        user.pin_created_at = timezone.now()
        user.save()

        # Generate wallet address and seed words
        wallet_data = generate_user_wallet(user)
        print(wallet_data)
        wallet_address = wallet_data["address"]
        seed_words = wallet_data["phrase"]
        print(wallet_address, seed_words)

        return JsonResponse({
            "message": "Wallet PIN and wallet created successfully",
            "userId": str(user.id),
            "pinCreatedAt": user.pin_created_at.isoformat(),
            "walletId": str(wallet_address),
            "walletAddress": wallet_address,
            "seedWords": seed_words
        }, status=200)

    except Exception as e:
        traceback.print_exc()

        return JsonResponse({"error": f"An unexpected error occurred: {str(e)}"}, status=500)

