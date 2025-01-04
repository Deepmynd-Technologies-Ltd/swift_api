from django.http import JsonResponse

def create_response(data, status=200):
    """
    Create a JSON response with the appropriate status code.
    """
    return JsonResponse(data, status=status, safe=isinstance(data, dict))
