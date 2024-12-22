from django.urls import path, include
from ninja import NinjaAPI
from .views import wallet_system
api = NinjaAPI()

api.add_router('wallet/', wallet_system)

urlpatterns = [
    path("", api.urls),
]