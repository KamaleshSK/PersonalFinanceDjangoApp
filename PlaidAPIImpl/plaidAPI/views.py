from rest_framework import generics, permissions, status
from rest_framework.response import Response
from knox.models import AuthToken
from .serializers import UserSerializer, RegisterSerializer
from django.contrib.auth import login, logout
from rest_framework.authtoken.serializers import AuthTokenSerializer
from knox.views import LoginView as KnoxLoginView
from knox.views import LogoutView as KnoxLogoutView

# Create your views here.


# Signup (Register) Endpoint
class RegisterAPI(generics.GenericAPIView):
    serializer_class = RegisterSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response({
            "user": UserSerializer(user, context=self.get_serializer_context()).data,
            "message": "Account successfully created"
        }, status=status.HTTP_201_CREATED)


# Login Endpoint
class LoginAPI(KnoxLoginView):
    # have to allow free access to the login endpoint
    permission_classes = [permissions.AllowAny]

    def post(self, request, format=None):
        serializer = AuthTokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        login(request, user)
        return super(LoginAPI, self).post(request, format=None)


# Logout
class UserLogoutAPIView(KnoxLogoutView):
    # can logout only if user already logged in
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, format=None):
        user = self.request.user
        # auth token deleted after user logout
        AuthToken.objects.filter(user=user).delete()
        logout(request)
        data = {'message': 'Successfully logged out'}
        return Response(data=data, status=status.HTTP_200_OK)
