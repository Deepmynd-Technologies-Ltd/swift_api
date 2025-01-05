from django.middleware.csrf import get_token
from django.http import JsonResponse


def create_response(data, status=200):
    """
    Create a JSON response with the appropriate status code.
    """
    return JsonResponse(data, status=status, safe=isinstance(data, dict))


def csrf_token_view(request):
    """
    Get the CSRF token for the current session.
    """
    token = get_token(request)
    return JsonResponse({'csrfToken': token})
