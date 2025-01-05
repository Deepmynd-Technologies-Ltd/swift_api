# views.py
from ninja import Router
from authentication.schemas import GoogleTokenDTO, ResponseDTO
from authentication.services import get_user_account, register_login

auth_router = Router(tags=["Authentication"])

@auth_router.get("/cron", auth=None)
def cron_job(request):
  return auth_router.api.create_response(request, {"good": "Work"}, status=200)

@auth_router.post("create-user/", response=ResponseDTO, auth=None)
def create_user(request, token:GoogleTokenDTO):
  res = register_login(token)
  # res = testing_login()
  return auth_router.api.create_response(request, res, status=res.status)

@auth_router.get("user/")
def get_user(request):
  user = request.user
  res = get_user_account(user)
  return auth_router.api.create_response(request, res, status=res.status)

