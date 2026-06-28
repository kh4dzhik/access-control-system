from django.db import models
from users.models import User


class Role(models.Model):
    """
    Роль пользователя - группа прав доступа.
    Каждая роль имеет свой скоуп (область видимости).
    """
    name = models.CharField(max_length=50, unique=True)  # Название роли
    description = models.TextField(blank=True)  # Описание

    # Тип доступа - определяет границы видимости ресурсов
    SCOPE_CHOICES = [
        ('GLOBAL', 'Global - all resources'),  # Видит всё
        ('DEPARTMENT', 'Only own department'),  # Только свой отдел
        ('OWNER', 'Only own objects'),  # Только свои объекты
        ('CUSTOM', 'Custom rules'),  # По кастомным правилам
    ]
    scope = models.CharField(max_length=20, choices=SCOPE_CHOICES, default='OWNER')

    def __str__(self):
        return self.name


class Permission(models.Model):
    """
    Конкретное разрешение - действие над ресурсом.
    Формат: resource:action (например, project:read)
    """
    name = models.CharField(max_length=100, unique=True)  # Уникальное имя
    resource_type = models.CharField(max_length=50)  # Тип ресурса (project, task, user...)
    action = models.CharField(max_length=20)  # Действие (create, read, update, delete)

    def __str__(self):
        return self.name


class UserRole(models.Model):
    """
    Связь пользователей с ролями.
    Один пользователь может иметь несколько ролей.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_roles')
    role = models.ForeignKey(Role, on_delete=models.CASCADE)
    assigned_at = models.DateTimeField(auto_now_add=True)  # Когда назначена

    class Meta:
        unique_together = ['user', 'role']  # Нельзя назначить одну роль дважды


class RolePermission(models.Model):
    """
    Связь ролей с разрешениями.
    Определяет, какие права есть у каждой роли.
    """
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name='role_permissions')
    permission = models.ForeignKey(Permission, on_delete=models.CASCADE)

    class Meta:
        unique_together = ['role', 'permission']


class AccessRule(models.Model):
    """
    ГЛАВНАЯ СУЩНОСТЬ - правила доступа к ресурсам.
    Здесь хранятся условия, по которым система определяет доступ.
    """
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name='access_rules')
    resource_type = models.CharField(max_length=50)  # К какому ресурсу применяется
    action = models.CharField(max_length=20)  # Какое действие проверяем

    # JSON-условие для фильтрации ресурсов
    # Пример: {"department": "{{user.department}}"} или {"owner_id": "{{user.id}}"}
    filter_condition = models.JSONField(default=dict, blank=True)

    is_active = models.BooleanField(default=True)  # Активно ли правило
    priority = models.IntegerField(default=0)  # Приоритет - чем выше, тем раньше проверяется

    def __str__(self):
        return f"{self.role.name} -> {self.resource_type}:{self.action}"


class AccessAuditLog(models.Model):
    """
    Лог всех проверок доступа.
    Используется для аудита и отладки системы.
    """
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    resource_type = models.CharField(max_length=50)  # К какому ресурсу был запрос
    resource_id = models.CharField(max_length=50, blank=True)  # ID конкретного ресурса
    action = models.CharField(max_length=20)  # Какое действие запрашивали
    decision = models.BooleanField()  # Разрешено (True) или запрещено (False)
    reason = models.TextField(blank=True)  # Почему принято такое решение
    ip_address = models.GenericIPAddressField(null=True, blank=True)  # IP пользователя
    created_at = models.DateTimeField(auto_now_add=True)  # Когда произошла проверка

    class Meta:
        # Индексы для быстрого поиска
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['resource_type', 'resource_id']),
        ]