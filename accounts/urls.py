from django.urls import re_path
from rest_framework_simplejwt.views import TokenRefreshView, TokenObtainPairView

from .views import UserList, SignInAPIView

urlpatterns = [
    re_path(r'^sign-in/?$', SignInAPIView.as_view(), name="sign-in"),
    re_path(r'^token/?$', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    re_path(r'^token/refresh/?$', TokenRefreshView.as_view(), name='token_refresh'),
    re_path(r'^users/?$', UserList.as_view(), name='user-list'),
]
