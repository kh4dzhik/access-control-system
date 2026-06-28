from rest_framework import serializers
from users.models import User
from auth_system.models import (
    Role, Permission, UserRole, RolePermission, AccessRule, AccessAuditLog
)


class RoleSerializer(serializers.ModelSerializer):
    """Сериализатор для ролей"""

    class Meta:
        model = Role
        fields = ['id', 'name', 'description', 'scope']
        read_only_fields = ['id']


class PermissionSerializer(serializers.ModelSerializer):
    """Сериализатор для разрешений"""

    class Meta:
        model = Permission
        fields = ['id', 'name', 'resource_type', 'action']
        read_only_fields = ['id']


class UserRoleSerializer(serializers.ModelSerializer):
    """Сериализатор для назначения ролей пользователям"""
    role_name = serializers.CharField(source='role.name', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)

    class Meta:
        model = UserRole
        fields = ['id', 'user', 'user_email', 'role', 'role_name', 'assigned_at']
        read_only_fields = ['id', 'assigned_at']


class RolePermissionSerializer(serializers.ModelSerializer):
    """Сериализатор для привязки разрешений к ролям"""
    permission_name = serializers.CharField(source='permission.name', read_only=True)

    class Meta:
        model = RolePermission
        fields = ['id', 'role', 'permission', 'permission_name']
        read_only_fields = ['id']


class AccessRuleSerializer(serializers.ModelSerializer):
    """
    Сериализатор для правил доступа.
    Самая важная часть системы - управление условиями.
    """
    role_name = serializers.CharField(source='role.name', read_only=True)

    class Meta:
        model = AccessRule
        fields = [
            'id', 'role', 'role_name', 'resource_type', 'action',
            'filter_condition', 'is_active', 'priority'
        ]
        read_only_fields = ['id']

    def validate_filter_condition(self, value):
        """Проверяем, что условие - валидный JSON объект"""
        if not isinstance(value, dict):
            raise serializers.ValidationError("Filter condition must be a JSON object")
        return value


class AccessAuditLogSerializer(serializers.ModelSerializer):
    """Сериализатор для аудит-лога"""
    user_email = serializers.CharField(source='user.email', read_only=True, default=None)

    class Meta:
        model = AccessAuditLog
        fields = [
            'id', 'user', 'user_email', 'resource_type', 'resource_id',
            'action', 'decision', 'reason', 'ip_address', 'created_at'
        ]
        read_only_fields = '__all__'


class UserDetailSerializer(serializers.ModelSerializer):
    """
    Детальный сериализатор пользователя с его ролями и правами
    """
    roles = serializers.SerializerMethodField()
    permissions = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'email', 'full_name', 'department',
            'is_active', 'is_staff', 'date_joined', 'roles', 'permissions'
        ]
        read_only_fields = ['id', 'date_joined']

    def get_roles(self, obj):
        """Получаем список ролей пользователя"""
        return [ur.role.name for ur in obj.user_roles.select_related('role')]

    def get_permissions(self, obj):
        """Получаем все разрешения пользователя через его роли"""
        permissions = set()
        for ur in obj.user_roles.select_related('role'):
            for rp in ur.role.role_permissions.select_related('permission'):
                permissions.add(rp.permission.name)
        return sorted(list(permissions))