import os
from celery.result import AsyncResult
from django.http import FileResponse
from rest_framework import status
from rest_framework.permissions import AllowAny

from rest_framework.response import Response
from rest_framework.views import APIView

from files.models import File
from root.celery import app




class FileStatusAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, task_id):
        task = AsyncResult(task_id, app=app)

        if task.state == "STARTED":
            return Response(data={"task_id": task_id, "status": task.state, "message": "Task was started!"},
                            status=status.HTTP_207_MULTI_STATUS)

        elif task.state == "SUCCESS":
            return Response(data={"task_id": task_id, "status": task.state, "result": task.result},
                            status=status.HTTP_207_MULTI_STATUS)

        elif task.state == "REVOKED":
            return Response(data={"task_id": task_id, "status": task.state, "message": "Task was revoked!"},
                            status=status.HTTP_207_MULTI_STATUS)

        elif task.state == "FAILURE":
            return Response(data={"task_id": task_id, "status": task.state, 'error': task.traceback},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            return Response(data={"task_id": task_id, "status": task.state, "message": "Task is still processing!"},
                            status=status.HTTP_207_MULTI_STATUS)



class FileTaskTerminateAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        task_ids = request.data.get("task_ids", None)

        if not task_ids:
            return Response({"error": "Task id is required!"}, status=status.HTTP_400_BAD_REQUEST)

        failure = []
        success = []

        for task_id in task_ids:
            try:
                app.control.revoke(task_id, terminate=True, signal="SIGKILL")
                success.append(task_id)
            except Exception as e:
                failure.append({task_id: str(e)})


        return Response(data={"success": success, "failure": failure}, status=status.HTTP_207_MULTI_STATUS)


class FileMediaAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, file_id):
        try:
            file_instance = File.objects.get(id=file_id)

            file_path = file_instance.file.path
            file_name = os.path.basename(file_path)

            response = FileResponse(open(file_path, 'rb'), as_attachment=True)
            response['Content-Disposition'] = f'attachment; filename="{file_name}"'

            return response

        except File.DoesNotExist:
            return Response({"error": "File does not exist"}, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

