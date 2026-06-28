from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    # Стандартная админка Django
    path('admin/', admin.site.urls),

    # API для авторизации и аутентификации
    path('api/auth/', include('auth_system.urls')),

    # Административное API (управление ролями, правами, правилами)
    path('api/admin/', include('auth_system.urls_admin')),
]