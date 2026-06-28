from django.urls import path, include
from rest_framework.routers import DefaultRouter
from auth_system.views_admin import (
    RoleViewSet, PermissionViewSet, UserRoleViewSet,
    AccessRuleViewSet, AccessAuditLogViewSet, AdminUserViewSet
)

# Создаем роутер для ViewSet'ов
router = DefaultRouter()
router.register(r'roles', RoleViewSet, basename='admin-role')
router.register(r'permissions', PermissionViewSet, basename='admin-permission')
router.register(r'user-roles', UserRoleViewSet, basename='admin-user-role')
router.register(r'access-rules', AccessRuleViewSet, basename='admin-access-rule')
router.register(r'audit-logs', AccessAuditLogViewSet, basename='admin-audit-log')
router.register(r'users', AdminUserViewSet, basename='admin-user')

urlpatterns = [
    path('', include(router.urls)),
]