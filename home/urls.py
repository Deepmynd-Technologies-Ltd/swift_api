from django.urls import path, include
from ninja import NinjaAPI
from .views import wallet_system
from .users import user_system

api = NinjaAPI()

api.add_router('wallet/', wallet_system)
api.add_router('user/', user_system)

urlpatterns = [
    path("", api.urls),
]