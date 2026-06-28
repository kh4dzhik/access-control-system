from rest_framework import serializers
from django.contrib.auth.hashers import make_password, check_password
from django.db import transaction
from users.models import User
from auth_system.models import UserRole, Role, AccessAuditLog
from rest_framework_simplejwt.tokens import RefreshToken


class RegisterSerializer(serializers.Serializer):
    """
    Сериализатор для регистрации нового пользователя
    """
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)
    full_name = serializers.CharField(max_length=255, required=False, allow_blank=True)

    def validate_email(self, value):
        """Проверяем, что email не занят"""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("User with this email already exists")
        return value.lower()

    def create(self, validated_data):
        """
        Создаем пользователя и назначаем ему роль USER по умолчанию
        """
        with transaction.atomic():
            # Хешируем пароль перед сохранением
            user = User.objects.create(
                email=validated_data['email'],
                full_name=validated_data.get('full_name', ''),
                password=make_password(validated_data['password']),
                is_active=True
            )

            # Назначаем роль USER (создаем если ее еще нет)
            default_role, _ = Role.objects.get_or_create(
                name='USER',
                defaults={'scope': 'OWNER', 'description': 'Default user role'}
            )
            UserRole.objects.create(user=user, role=default_role)

            return user


class LoginSerializer(serializers.Serializer):
    """
    Сериализатор для входа в систему
    """
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        """
        Проверяем учетные данные и возвращаем токены
        """
        email = data.get('email', '').lower()
        password = data.get('password', '')

        # 1. Проверяем существование пользователя
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            # Логируем неудачную попытку
            AccessAuditLog.objects.create(
                user=None,
                resource_type='auth',
                resource_id=email,
                action='login',
                decision=False,
                reason=f'User not found: {email}',
                ip_address=self.context.get('request').META.get('REMOTE_ADDR')
            )
            raise serializers.ValidationError("Invalid credentials")

        # 2. Проверяем активен ли пользователь
        if not user.is_active:
            AccessAuditLog.objects.create(
                user=user,
                resource_type='auth',
                resource_id=str(user.id),
                action='login',
                decision=False,
                reason='Account is deactivated',
                ip_address=self.context.get('request').META.get('REMOTE_ADDR')
            )
            raise serializers.ValidationError("Account is deactivated")

        # 3. Проверяем пароль
        if not check_password(password, user.password):
            AccessAuditLog.objects.create(
                user=user,
                resource_type='auth',
                resource_id=str(user.id),
                action='login',
                decision=False,
                reason='Invalid password',
                ip_address=self.context.get('request').META.get('REMOTE_ADDR')
            )
            raise serializers.ValidationError("Invalid credentials")

        # 4. Генерируем JWT токены
        refresh = RefreshToken.for_user(user)

        # 5. Логируем успешный вход
        AccessAuditLog.objects.create(
            user=user,
            resource_type='auth',
            resource_id=str(user.id),
            action='login',
            decision=True,
            reason='Successful login',
            ip_address=self.context.get('request').META.get('REMOTE_ADDR')
        )

        self.context['user'] = user

        # Возвращаем данные пользователя и токены
        return {
            'user': {
                'id': user.id,
                'email': user.email,
                'full_name': user.full_name,
                'department': user.department
            },
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }


class LogoutSerializer(serializers.Serializer):
    """
    Сериализатор для выхода из системы
    """
    refresh = serializers.CharField()

    def validate_refresh(self, value):
        """
        Проверяем валидность refresh токена и логируем выход
        """
        try:
            token = RefreshToken(value)
            user_id = token.payload.get('user_id')
            if user_id:
                user = User.objects.filter(id=user_id).first()
                if user:
                    self.context['user'] = user
                    AccessAuditLog.objects.create(
                        user=user,
                        resource_type='auth',
                        resource_id=str(user.id),
                        action='logout',
                        decision=True,
                        reason='User logged out',
                        ip_address=self.context.get('request').META.get('REMOTE_ADDR')
                    )
        except Exception:
            raise serializers.ValidationError("Invalid refresh token")
        return value