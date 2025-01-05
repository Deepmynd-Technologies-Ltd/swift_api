# urls.py

from django.urls import path, include
from ninja import NinjaAPI
from .views import auth_router
from wallet.views import wallet_router
from webhook.views import webhook
from ninja_jwt.authentication import JWTAuth
from django.contrib.admin.views.decorators import staff_member_required

api = NinjaAPI()
# api = NinjaAPI(auth=JWTAuth(),docs_decorator=staff_member_required)

api.add_router("auth/", auth_router)
# api.add_router("wallet/", wallet_router)
# api.add_router("webhook/", webhook)

urlpatterns = [
    path("", api.urls),
]