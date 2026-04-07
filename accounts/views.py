from drf_spectacular.utils import extend_schema
from rest_framework import generics, permissions
from rest_framework_simplejwt.views import TokenObtainPairView

from .serializers import RegisterSerializer, UserSerializer


class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = (permissions.AllowAny,)

    def get_queryset(self):
        from .models import User

        return User.objects.none()

    @extend_schema(summary="Register a standard user account")
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class MeView(generics.RetrieveAPIView):
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user

    @extend_schema(summary="Current user profile")
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class TokenObtainPairViewSchema(TokenObtainPairView):
    @extend_schema(summary="Obtain JWT access & refresh tokens")
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)
