"""
URL configuration for core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
"""
URL configuration for core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from home import users

urlpatterns = [
    path('admin/', admin.site.urls),
    path("api/", include("home.urls")),
    path('api/register/', users.register_user, name='register_user'),  # Fixed: Added view function
    path('api/login/', users.login_user, name='login_user'),  # Fixed: Added view function
    path('users/', users.get_all_users, name='get_all_users'),
    path('api/createpin', users.create_pin, name='create_and_confirm_pin'),
    path('user/<int:user_id>/', users.get_user_by_id, name='get_user_by_id'),  # Fixed: Added parameter
    path('user/<int:user_id>/delete/', users.delete_user_by_id, name='delete_user_by_id'),  # Fixed: Added parameter
    path('user/<int:user_id>/update/', users.update_user_by_id, name='update_user_by_id'),  # Fixed: Added parameter
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)