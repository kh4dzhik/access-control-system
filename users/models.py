from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.utils import timezone
from .managers import UserManager  # Импортируем менеджер


# Кастомная модель пользователя с email в качестве логина.
class User(AbstractBaseUser, PermissionsMixin):

    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=255)
    department = models.CharField(max_length=100, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)

    # Используем email как поле для входа
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['full_name']

    # Привязываем кастомный менеджер
    objects = UserManager()

    def __str__(self):
        return self.email

    def natural_key(self):
        """
        Возвращает natural key для сериализации.
        """
        return (self.email,)