from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.views import APIView
from django.contrib.auth import login, logout
from django.utils import timezone
from django.db import transaction
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.utils.crypto import get_random_string
from django.utils import timezone
from datetime import timedelta

from .models import User, UserSession, PasswordResetToken
from .serializers import (
    UserSerializer, UserCreateSerializer, UserUpdateSerializer,
    ChangePasswordSerializer, LoginSerializer, UserSessionSerializer,
    PasswordResetRequestSerializer, PasswordResetConfirmSerializer
)


class UserListView(generics.ListCreateAPIView):
    """List and create users."""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAdminUser]
    filterset_fields = ['role', 'department', 'is_active']
    search_fields = ['username', 'first_name', 'last_name', 'email', 'employee_id']
    ordering_fields = ['username', 'first_name', 'last_name', 'created_at']
    ordering = ['username']


class UserDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or delete a user."""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_permissions(self):
        if self.request.method in ['PUT', 'PATCH', 'DELETE']:
            return [permissions.IsAdminUser]
        return [permissions.IsAuthenticated]


class UserCreateView(generics.CreateAPIView):
    """Create a new user."""
    serializer_class = UserCreateSerializer
    permission_classes = [permissions.IsAdminUser]


class UserUpdateView(generics.UpdateAPIView):
    """Update user information."""
    queryset = User.objects.all()
    serializer_class = UserUpdateSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_permissions(self):
        if self.request.user.role == 'admin':
            return [permissions.IsAuthenticated]
        # Users can only update their own information
        return [permissions.IsAuthenticated]
    
    def get_object(self):
        if self.request.user.role == 'admin':
            return super().get_object()
        return self.request.user


class ChangePasswordView(APIView):
    """Change user password."""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            user = request.user
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            return Response({'message': 'Password changed successfully'})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    """User login view."""
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            login(request, user)
            
            # Create or get token
            token, created = Token.objects.get_or_create(user=user)
            
            # Track session
            session = UserSession.objects.create(
                user=user,
                session_key=request.session.session_key or get_random_string(40),
                ip_address=self._get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            # Update user's last login IP
            user.last_login_ip = self._get_client_ip(request)
            user.save(update_fields=['last_login_ip'])
            
            return Response({
                'token': token.key,
                'user': UserSerializer(user).data,
                'message': 'Login successful'
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def _get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class LogoutView(APIView):
    """User logout view."""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        # End current session
        try:
            session = UserSession.objects.get(
                user=request.user,
                session_key=request.session.session_key,
                is_active=True
            )
            session.logout_time = timezone.now()
            session.is_active = False
            session.save()
        except UserSession.DoesNotExist:
            pass
        
        # Delete token
        try:
            request.user.auth_token.delete()
        except:
            pass
        
        logout(request)
        return Response({'message': 'Logout successful'})


class CurrentUserView(APIView):
    """Get current authenticated user information."""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)


class PasswordResetRequestView(APIView):
    """Request password reset."""
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            try:
                user = User.objects.get(email=email, is_active=True)
                
                # Create reset token
                token = get_random_string(64)
                expires_at = timezone.now() + timedelta(hours=24)
                
                PasswordResetToken.objects.create(
                    user=user,
                    token=token,
                    expires_at=expires_at
                )
                
                # TODO: Send email with reset link
                # For now, just return the token (in production, send via email)
                
                return Response({
                    'message': 'Password reset email sent',
                    'token': token  # Remove this in production
                })
                
            except User.DoesNotExist:
                return Response({
                    'message': 'If an account with this email exists, a password reset email has been sent.'
                })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PasswordResetConfirmView(APIView):
    """Confirm password reset."""
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        if serializer.is_valid():
            token = serializer.validated_data['token']
            new_password = serializer.validated_data['new_password']
            
            try:
                reset_token = PasswordResetToken.objects.get(
                    token=token,
                    is_used=False,
                    expires_at__gt=timezone.now()
                )
                
                # Update password
                user = reset_token.user
                user.set_password(new_password)
                user.save()
                
                # Mark token as used
                reset_token.is_used = True
                reset_token.save()
                
                return Response({'message': 'Password reset successful'})
                
            except PasswordResetToken.DoesNotExist:
                return Response({
                    'error': 'Invalid or expired reset token'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserSessionListView(generics.ListAPIView):
    """List user sessions for audit purposes."""
    queryset = UserSession.objects.all()
    serializer_class = UserSessionSerializer
    permission_classes = [permissions.IsAdminUser]
    filterset_fields = ['user', 'is_active', 'login_time']
    ordering = ['-login_time']


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def user_permissions(request):
    """Get current user's permissions."""
    user = request.user
    permissions = {
        'can_create': user.has_ipsas_permission('create'),
        'can_edit': user.has_ipsas_permission('edit'),
        'can_delete': user.has_ipsas_permission('delete'),
        'can_view': user.has_ipsas_permission('view'),
        'can_audit': user.has_ipsas_permission('audit'),
        'can_approve': user.has_ipsas_permission('approve'),
        'role': user.role,
        'is_admin': user.is_superuser or user.role == 'admin'
    }
    return Response(permissions)
