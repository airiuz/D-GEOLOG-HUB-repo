from django.contrib.auth import authenticate
from django.middleware import csrf
from rest_framework.response import Response
from rest_framework_simplejwt import tokens
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.tokens import RefreshToken

from root import settings
from .models import CustomUser
from .serializers import UserSerializer, SignInSerializer

from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView





class UserList(generics.ListCreateAPIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    queryset = CustomUser.objects.all()
    serializer_class = UserSerializer


class SignInAPIView(APIView):

    def post(self, request, *args, **kwargs):
        # Get the username and password from the request
        username = request.data.get('email')
        password = request.data.get('password')

        # Authenticate the user
        user = authenticate(email=username, password=password)

        # If authentication is successful, generate tokens
        if user is not None:
            refresh = RefreshToken.for_user(user)

            # Return both access and refresh tokens in the response
            return Response({
                'access': str(refresh.access_token),
                'refresh': str(refresh),
            }, status=status.HTTP_200_OK)

        # If authentication fails, return an error
        return Response({"detail": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)
    # def post(self, request):
    #     serializer = SignInSerializer(data=request.data)
    #
    #     if serializer.is_valid():
    #         email = serializer.validated_data["email"]
    #         password = serializer.validated_data["password"]
    #
    #         user = authenticate(email=email, password=password)
    #
    #         if user is not None:
    #             refresh = RefreshToken.for_user(user)
    #             res = Response()
    #             #     res.set_cookie(
    #             #         key=settings.SIMPLE_JWT['AUTH_COOKIE'],
    #             #         value=tokens["access_token"],
    #             #         expires=settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'],
    #             #         secure=settings.SIMPLE_JWT['AUTH_COOKIE_SECURE'],
    #             #         httponly=settings.SIMPLE_JWT['AUTH_COOKIE_HTTP_ONLY'],
    #             #         samesite=settings.SIMPLE_JWT['AUTH_COOKIE_SAMESITE'],
    #             #     )
    #             #     res.set_cookie(
    #             #         key=settings.SIMPLE_JWT['AUTH_COOKIE_REFRESH'],
    #             #         value=tokens["refresh_token"],
    #             #         expires=settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'],
    #             #         secure=settings.SIMPLE_JWT['AUTH_COOKIE_SECURE'],
    #             #         httponly=settings.SIMPLE_JWT['AUTH_COOKIE_HTTP_ONLY'],
    #             #         samesite=settings.SIMPLE_JWT['AUTH_COOKIE_SAMESITE'],
    #             #     )
    #             #
    #             return Response({
    #                 'access': str(refresh.access_token),
    #                 'refresh': str(refresh),
    #             }, status=status.HTTP_200_OK)
    #
    #         return Response(data={"error": "Invalid credentials"}, status=status.HTTP_400_BAD_REQUEST)
    #
    #     return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)
