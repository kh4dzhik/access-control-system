from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404
from users.models import User
from auth_system.models import (
    Role, Permission, UserRole, RolePermission, AccessRule, AccessAuditLog
)
from auth_system.serializers_admin import (
    RoleSerializer, PermissionSerializer, UserRoleSerializer,
    RolePermissionSerializer, AccessRuleSerializer,
    AccessAuditLogSerializer, UserDetailSerializer
)
from auth_system.permissions import IsAdminUser


class RoleViewSet(ModelViewSet):
    """
    Управление ролями. Только для администраторов.
    """
    permission_classes = [IsAuthenticated, IsAdminUser]
    queryset = Role.objects.all()
    serializer_class = RoleSerializer


class PermissionViewSet(ModelViewSet):
    """
    Управление разрешениями. Только для администраторов.
    """
    permission_classes = [IsAuthenticated, IsAdminUser]
    queryset = Permission.objects.all()
    serializer_class = PermissionSerializer


class UserRoleViewSet(ModelViewSet):
    """
    Управление назначением ролей пользователям.
    """
    permission_classes = [IsAuthenticated, IsAdminUser]
    queryset = UserRole.objects.all()
    serializer_class = UserRoleSerializer


class AccessRuleViewSet(ModelViewSet):
    """
    Управление правилами доступа.
    Это основной инструмент для настройки разграничения доступа.
    """
    permission_classes = [IsAuthenticated, IsAdminUser]
    queryset = AccessRule.objects.all().select_related('role')
    serializer_class = AccessRuleSerializer


class AccessAuditLogViewSet(ModelViewSet):
    """
    Просмотр логов проверок доступа.
    Позволяет отслеживать все запросы к системе.
    """
    permission_classes = [IsAuthenticated, IsAdminUser]
    queryset = AccessAuditLog.objects.all().select_related('user').order_by('-created_at')
    serializer_class = AccessAuditLogSerializer

    def get_queryset(self):
        """
        Фильтрация логов по параметрам запроса
        """
        queryset = super().get_queryset()

        # Фильтр по пользователю
        user_id = self.request.query_params.get('user_id')
        if user_id:
            queryset = queryset.filter(user_id=user_id)

        # Фильтр по типу ресурса
        resource_type = self.request.query_params.get('resource_type')
        if resource_type:
            queryset = queryset.filter(resource_type=resource_type)

        # Фильтр по решению (разрешено/запрещено)
        decision = self.request.query_params.get('decision')
        if decision is not None:
            queryset = queryset.filter(decision=decision.lower() == 'true')

        return queryset


class AdminUserViewSet(ModelViewSet):
    """
    Управление пользователями для администраторов.
    """
    permission_classes = [IsAuthenticated, IsAdminUser]
    queryset = User.objects.all()
    serializer_class = UserDetailSerializer

    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """
        Активация пользователя (установить is_active=True)
        """
        user = self.get_object()
        user.is_active = True
        user.save(update_fields=['is_active'])
        return Response({'message': f'User {user.email} activated'})

    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        """
        Деактивация пользователя (установить is_active=False)
        Пользователь не сможет войти, но запись останется в БД
        """
        user = self.get_object()
        # Запрещаем деактивировать самого себя
        if user.id == request.user.id:
            return Response({'error': 'Cannot deactivate yourself'}, status=status.HTTP_400_BAD_REQUEST)

        user.is_active = False
        user.save(update_fields=['is_active'])
        return Response({'message': f'User {user.email} deactivated'})