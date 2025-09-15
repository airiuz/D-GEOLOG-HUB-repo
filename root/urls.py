from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from root import settings
from drf_yasg.generators import OpenAPISchemaGenerator
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

schema_view = get_schema_view(
   openapi.Info(
      title="Ocr Swagger",
      default_version='v1',
      description="Test description",
      terms_of_service="https://www.google.com/policies/terms/",
      contact=openapi.Contact(email="contact@yourapi.local"),
      license=openapi.License(name="BSD License"),
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
)

patterns = [
    path('admin/', admin.site.urls),
    path('', include([
        path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
        path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
        path('swagger.json', schema_view.without_ui(cache_timeout=0), name='schema-json'),
        path('auth/', include('accounts.urls')),
        path('file/', include('files.urls')),
        path('uzgashkliti/', include('uzgashkliti.urls')),
    ])),
]

urlpatterns = [
    path('api/', include(patterns))
]


urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
