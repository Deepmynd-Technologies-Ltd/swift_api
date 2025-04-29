from django.urls import path, include
from ninja import NinjaAPI
from .views import wallet_system
from provider.views import provider_system
# from swap.swap_views import swap_router
api = NinjaAPI()

api.add_router('wallet/', wallet_system)
api.add_router('provider/', provider_system)
# api.add_router('swap/', swap_router)


urlpatterns = [
    path("", api.urls),
]