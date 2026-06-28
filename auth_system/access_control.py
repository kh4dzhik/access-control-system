from django.db.models import Q
from auth_system.models import AccessRule, AccessAuditLog


class AccessController:
    """
    Основной контроллер проверки доступа.
    Здесь реализована вся логика принятия решений.
    """

    @staticmethod
    def check_permission(user, resource_type, action, resource_instance=None):
        """
        Проверяет, имеет ли пользователь доступ к ресурсу.
        Возвращает (результат, причина).
        """
        # Суперюзер имеет доступ ко всему
        if user.is_superuser:
            AccessController._log_decision(user, resource_type, action, True, "Superuser")
            return True, "Superuser granted"

        # Получаем все роли пользователя
        user_roles = user.user_roles.select_related('role').all()
        role_ids = [ur.role_id for ur in user_roles]

        # Если у пользователя нет ролей - доступ запрещен
        if not role_ids:
            AccessController._log_decision(user, resource_type, action, False, "No roles")
            return False, "User has no roles"

        # Ищем правила доступа для ролей пользователя
        rules = AccessRule.objects.filter(
            role_id__in=role_ids,
            resource_type=resource_type,
            action=action,
            is_active=True
        ).select_related('role').order_by('-priority')  # Сортируем по приоритету

        # Если правил нет - доступ запрещен
        if not rules.exists():
            AccessController._log_decision(user, resource_type, action, False, "No matching rules")
            return False, f"No access rules for {resource_type}:{action}"

        # Проверяем правила по порядку приоритета
        for rule in rules:
            # 1. Глобальный доступ - разрешаем сразу
            if rule.role.scope == 'GLOBAL':
                AccessController._log_decision(user, resource_type, action, True, "Global scope")
                return True, "Access granted by global scope"

            # 2. Доступ только к своим объектам
            elif rule.role.scope == 'OWNER':
                # Если передан конкретный объект - проверяем владельца
                if resource_instance and hasattr(resource_instance, 'owner_id'):
                    if resource_instance.owner_id == user.id:
                        AccessController._log_decision(user, resource_type, action, True, "Owner")
                        return True, "Access granted: resource owner"
                    else:
                        AccessController._log_decision(user, resource_type, action, False, "Not owner")
                        return False, "You don't own this resource"
                else:
                    # Для списков разрешаем, фильтр будет применен позже
                    AccessController._log_decision(user, resource_type, action, True, "Owner list")
                    return True, "Access granted for list operation"

            # 3. Доступ только к ресурсам своего отдела
            elif rule.role.scope == 'DEPARTMENT':
                if resource_instance and hasattr(resource_instance, 'department'):
                    if resource_instance.department == user.department:
                        AccessController._log_decision(user, resource_type, action, True, "Same department")
                        return True, "Access granted: same department"
                    else:
                        AccessController._log_decision(user, resource_type, action, False, "Different department")
                        return False, "Resource belongs to another department"
                else:
                    return True, "Department scope: apply filter later"

            # 4. Кастомные правила с JSON-условиями
            elif rule.role.scope == 'CUSTOM':
                condition = rule.filter_condition
                if not condition:
                    AccessController._log_decision(user, resource_type, action, True, "Empty custom rule")
                    return True, "Custom rule granted"

                # Подставляем переменные пользователя в условие
                evaluated = AccessController._evaluate_condition(condition, user)

                # Если передан объект - проверяем соответствует ли он условию
                if resource_instance:
                    if AccessController._matches_condition(resource_instance, evaluated):
                        AccessController._log_decision(user, resource_type, action, True, "Custom matched")
                        return True, "Custom rule matched"
                else:
                    # Для списков возвращаем условие для фильтрации
                    AccessController._log_decision(user, resource_type, action, True, "Custom filter")
                    return True, evaluated

        # Если ни одно правило не подошло - доступ запрещен
        AccessController._log_decision(user, resource_type, action, False, "No rule granted")
        return False, "Access denied by all rules"

    @staticmethod
    def _evaluate_condition(condition, user):
        """
        Подставляет переменные пользователя в JSON-условие.
        Поддерживает {{user.id}}, {{user.department}}, {{user.email}}
        """
        import json
        condition_str = json.dumps(condition)
        condition_str = condition_str.replace('{{user.id}}', str(user.id))
        condition_str = condition_str.replace('{{user.department}}', user.department or '')
        condition_str = condition_str.replace('{{user.email}}', user.email)
        return json.loads(condition_str)

    @staticmethod
    def _matches_condition(instance, condition):
        """
        Проверяет, соответствует ли объект условию.
        Сравнивает атрибуты объекта с значениями в условии.
        """
        for key, value in condition.items():
            if hasattr(instance, key):
                if getattr(instance, key) != value:
                    return False
        return True

    @staticmethod
    def _log_decision(user, resource_type, action, decision, reason):
        """
        Записывает решение о доступе в лог.
        """
        try:
            AccessAuditLog.objects.create(
                user=user,
                resource_type=resource_type,
                action=action,
                decision=decision,
                reason=reason[:500]  # Ограничиваем длину
            )
        except:
            pass  # Не даем упасть системе из-за ошибки логирования

    @staticmethod
    def apply_access_filter(user, resource_type, action, queryset):
        """
        Применяет фильтры доступа к запросу на получение списка.
        Это ключевой метод для row-level security.
        """
        # Получаем роли пользователя
        user_roles = user.user_roles.select_related('role').all()
        role_ids = [ur.role_id for ur in user_roles]

        # Ищем правила
        rules = AccessRule.objects.filter(
            role_id__in=role_ids,
            resource_type=resource_type,
            action=action,
            is_active=True
        ).order_by('-priority')

        # Если правил нет - возвращаем пустой queryset
        if not rules:
            return queryset.none()

        # Собираем все условия в один Q-объект
        conditions = Q()
        for rule in rules:
            if rule.role.scope == 'CUSTOM' and rule.filter_condition:
                condition = AccessController._evaluate_condition(rule.filter_condition, user)
                conditions |= Q(**condition)
            elif rule.role.scope == 'DEPARTMENT':
                conditions |= Q(department=user.department)
            elif rule.role.scope == 'OWNER':
                conditions |= Q(owner_id=user.id)
            elif rule.role.scope == 'GLOBAL':
                # Глобальный доступ - возвращаем все записи
                return queryset

        # Применяем фильтр и убираем дубликаты
        if conditions:
            return queryset.filter(conditions).distinct()
        return queryset.none()