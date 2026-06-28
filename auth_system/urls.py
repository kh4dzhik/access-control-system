from django.urls import path
from auth_system.views import (
    RegisterView, LoginView, LogoutView, RefreshTokenView, CurrentUserView
)

urlpatterns = [
    # Регистрация нового пользователя
    path('register/', RegisterView.as_view(), name='register'),

    # Вход в систему
    path('login/', LoginView.as_view(), name='login'),

    # Выход из системы
    path('logout/', LogoutView.as_view(), name='logout'),

    # Обновление access токена
    path('refresh/', RefreshTokenView.as_view(), name='refresh'),

    # Текущий пользователь
    path('me/', CurrentUserView.as_view(), name='current_user'),
]