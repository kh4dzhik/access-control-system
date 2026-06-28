from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from users.models import User
from auth_system.serializers import RegisterSerializer, LoginSerializer, LogoutSerializer


class RegisterView(APIView):
    """
    Регистрация нового пользователя.
    Доступно всем, даже неавторизованным.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        user = serializer.save()
        return Response({
            'message': 'User registered successfully',
            'user': {'id': user.id, 'email': user.email, 'full_name': user.full_name}
        }, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    """
    Вход в систему по email и паролю.
    Возвращает access и refresh токены.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={'request': request})
        if not serializer.is_valid():
            return Response({'errors': serializer.errors}, status=status.HTTP_401_UNAUTHORIZED)

        return Response(serializer.validated_data, status=status.HTTP_200_OK)


class LogoutView(APIView):
    """
    Выход из системы.
    Добавляет refresh токен в черный список.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = LogoutSerializer(data=request.data, context={'request': request})
        if not serializer.is_valid():
            return Response({'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        # Добавляем токен в черный список
        try:
            refresh_token = request.data.get('refresh')
            token = RefreshToken(refresh_token)
            token.blacklist()
        except:
            pass  # Если blacklist не настроен, просто игнорируем

        return Response({'message': 'Logged out successfully'}, status=status.HTTP_200_OK)


class RefreshTokenView(APIView):
    """
    Обновление access токена с помощью refresh токена.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        refresh_token = request.data.get('refresh')
        if not refresh_token:
            return Response({'error': 'Refresh token required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            refresh = RefreshToken(refresh_token)
            return Response({'access': str(refresh.access_token)}, status=status.HTTP_200_OK)
        except Exception:
            return Response({'error': 'Invalid refresh token'}, status=status.HTTP_401_UNAUTHORIZED)


class CurrentUserView(APIView):
    """
    Получение информации о текущем авторизованном пользователе.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        return Response({
            'id': user.id,
            'email': user.email,
            'full_name': user.full_name,
            'department': user.department,
            'is_active': user.is_active,
            'is_staff': user.is_staff,
            'date_joined': user.date_joined,
            'roles': [ur.role.name for ur in user.user_roles.select_related('role')]
        })