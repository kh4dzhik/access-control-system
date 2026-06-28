from django.contrib.auth.backends import BaseBackend
from users.models import User


class CustomAuthBackend(BaseBackend):
    """
    Собственный бэкенд аутентификации.
    Проверяем пользователя по email и паролю, а также проверяем активность.
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        """
        Основной метод аутентификации.
        username в нашем случае - это email.
        """
        try:
            # Ищем пользователя по email (приводим к нижнему регистру)
            user = User.objects.get(email=username.lower())

            # Проверяем пароль и активность пользователя
            if user.check_password(password) and user.is_active:
                return user
        except User.DoesNotExist:
            return None

    def get_user(self, user_id):
        """
        Получение пользователя по ID.
        Возвращаем только активных пользователей.
        """
        try:
            return User.objects.get(pk=user_id, is_active=True)
        except User.DoesNotExist:
            return None