from django.urls import re_path
from files.views import FileStatusAPIView, FileTaskTerminateAPIView, FileMediaAPIView

app_name = 'files'

urlpatterns = [
    re_path(r'^status/(?P<task_id>[\w-]+)/?$', FileStatusAPIView.as_view(), name="file_status"),
    re_path(r'^download/(?P<file_id>[\w-]+)/?$', FileMediaAPIView.as_view(), name="media_file"),
    re_path(r'^terminate/?$', FileTaskTerminateAPIView.as_view(), name='terminate_task'),
]
