from rest_framework.permissions import BasePermission
from auth_system.access_control import AccessController


class CustomPermission(BasePermission):
    """
    Кастомный класс разрешений для DRF.
    Интегрирует нашу систему доступа с фреймворком.
    """

    def has_permission(self, request, view):
        """
        Проверка доступа на уровне запроса (список, создание)
        """
        user = request.user

        # Пользователь должен быть авторизован
        if not user or not user.is_authenticated:
            return False

        # Определяем тип ресурса из вьюхи
        resource_type = getattr(view, 'resource_type', view.__class__.__name__.lower().replace('viewset', ''))

        # Определяем действие
        action = self._get_action(view, request)

        # Для списков проверяем право на чтение
        if action == 'list':
            result, _ = AccessController.check_permission(user, resource_type, 'read')
            return result

        # Для создания проверяем право на создание
        elif action == 'create':
            result, _ = AccessController.check_permission(user, resource_type, 'create')
            return result

        # Для остальных действий проверяем на уровне объекта
        return True

    def has_object_permission(self, request, view, obj):
        """
        Проверка доступа к конкретному объекту.
        Вызывается для GET /id/, PUT, PATCH, DELETE
        """
        user = request.user
        resource_type = getattr(view, 'resource_type', obj.__class__.__name__.lower())

        # Определяем действие по HTTP методу
        if request.method == 'GET':
            action = 'read'
        elif request.method in ['PUT', 'PATCH']:
            action = 'update'
        elif request.method == 'DELETE':
            action = 'delete'
        else:
            action = 'execute'

        # Проверяем доступ к объекту
        result, _ = AccessController.check_permission(user, resource_type, action, obj)
        return result

    def _get_action(self, view, request):
        """
        Определяет действие на основе вьюхи и метода запроса
        """
        # Если во вьюхе явно указано действие (для ViewSet)
        if hasattr(view, 'action'):
            return view.action

        # Маппинг HTTP методов на действия
        method_map = {
            'GET': 'list' if not hasattr(view, 'lookup_url_kwarg') else 'retrieve',
            'POST': 'create',
            'PUT': 'update',
            'PATCH': 'partial_update',
            'DELETE': 'destroy',
        }
        return method_map.get(request.method, 'unknown')


class IsAdminUser(BasePermission):
    """
    Проверка, что пользователь является администратором.
    Используется для защиты административных эндпоинтов.
    """

    def has_permission(self, request, view):
        # Пользователь должен быть авторизован
        if not request.user or not request.user.is_authenticated:
            return False

        # Проверяем наличие роли ADMIN через БД
        from auth_system.models import UserRole
        return UserRole.objects.filter(
            user=request.user,
            role__name='ADMIN'
        ).exists()