import os
import uuid

from django.core.files.base import ContentFile
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import AllowAny

from rest_framework.response import Response

from files.models import File
from files.serializers import Pdf2HtmlSerializer, Json2HtmlSerializer, Pdf2DocxSerializer, Json2DocxSerializer, \
    Docx2HtmlSerializer
from uzgashkliti.tasks import pdf2html_task, json2html_task, pdf2docx_task, json2docx_task, docx2html_task, pdf2json_task



class Pdf2JsonView(GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = Pdf2HtmlSerializer
    parser_classes = [MultiPartParser]

    @swagger_auto_schema(operation_description='Upload file...', )
    def post(self, request):
        files = request.FILES.getlist("file")

        if len(files) > 0:
            task_ids = []
            for f in files:
                serializer = self.serializer_class(data={"file": f})
                if serializer.is_valid():
                    unique_filename = f"{uuid.uuid4()}{os.path.splitext(f.name)[1]}"
                    file = File()
                    file.file.save(unique_filename, ContentFile(f.read()))
                    task = pdf2json_task.delay(file.id)
                    task_ids.append(task.id)

                else:
                    return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            return Response(data=task_ids, status=status.HTTP_202_ACCEPTED)

        return Response(data={"error": "File does not exist"}, status=status.HTTP_400_BAD_REQUEST)


class Pdf2HtmlView(GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = Pdf2HtmlSerializer
    parser_classes = [MultiPartParser]

    @swagger_auto_schema(operation_description='Upload file...', )
    def post(self, request):
        files = request.FILES.getlist("file")

        if len(files) > 0:
            task_ids = []
            for f in files:
                serializer = self.serializer_class(data={"file": f})
                if serializer.is_valid():
                    unique_filename = f"{uuid.uuid4()}{os.path.splitext(f.name)[1]}"
                    file = File()
                    file.file.save(unique_filename, ContentFile(f.read()))
                    task = pdf2html_task.delay(file.id)
                    task_ids.append(task.id)

                else:
                    return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            return Response(data=task_ids, status=status.HTTP_202_ACCEPTED)

        return Response(data={"error": "File does not exist"}, status=status.HTTP_400_BAD_REQUEST)


class Json2HtmlView(GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = Json2HtmlSerializer
    parser_classes = [MultiPartParser]

    @swagger_auto_schema(operation_description='Upload file...', )
    def post(self, request):
        files = request.FILES.getlist("file")

        if len(files) > 0:
            task_ids = []
            for f in files:
                serializer = self.serializer_class(data={"file": f})
                if serializer.is_valid():
                    unique_filename = f"{uuid.uuid4()}{os.path.splitext(f.name)[1]}"
                    file = File()
                    file.file.save(unique_filename, ContentFile(f.read()))
                    task = json2html_task.delay(file.id)
                    task_ids.append(task.id)

                else:
                    return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            return Response(data=task_ids, status=status.HTTP_202_ACCEPTED)

        return Response(data={"error": "File does not exist"}, status=status.HTTP_400_BAD_REQUEST)



class Pdf2DocxView(GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = Pdf2DocxSerializer
    parser_classes = [MultiPartParser]

    @swagger_auto_schema(operation_description='Upload file...', )
    def post(self, request):
        files = request.FILES.getlist("file")

        if len(files) > 0:
            task_ids = []
            for f in files:
                serializer = self.serializer_class(data={"file": f})
                if serializer.is_valid():
                    unique_filename = f"{uuid.uuid4()}{os.path.splitext(f.name)[1]}"
                    file = File()
                    file.file.save(unique_filename, ContentFile(f.read()))
                    task = pdf2docx_task.delay(file.id)
                    task_ids.append(task.id)

                else:
                    return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            return Response(data=task_ids, status=status.HTTP_202_ACCEPTED)

        return Response(data={"error": "File does not exist"}, status=status.HTTP_400_BAD_REQUEST)


class Json2DocxView(GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = Json2DocxSerializer
    parser_classes = [MultiPartParser]

    @swagger_auto_schema(operation_description='Upload file...', )
    def post(self, request):
        files = request.FILES.getlist("file")

        if len(files) > 0:
            task_ids = []
            for f in files:
                serializer = self.serializer_class(data={"file": f})
                if serializer.is_valid():
                    unique_filename = f"{uuid.uuid4()}{os.path.splitext(f.name)[1]}"
                    file = File()
                    file.file.save(unique_filename, ContentFile(f.read()))
                    task = json2docx_task.delay(file.id)
                    task_ids.append(task.id)

                else:
                    return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            return Response(data=task_ids, status=status.HTTP_202_ACCEPTED)

        return Response(data={"error": "File does not exist"}, status=status.HTTP_400_BAD_REQUEST)

class Docx2HtmlView(GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = Docx2HtmlSerializer
    parser_classes = [MultiPartParser]

    @swagger_auto_schema(operation_description='Upload file...', )
    def post(self, request):
        files = request.FILES.getlist("file")

        if len(files) > 0:
            task_ids = []
            for f in files:
                serializer = self.serializer_class(data={"file": f})
                if serializer.is_valid():
                    unique_filename = f"{uuid.uuid4()}{os.path.splitext(f.name)[1]}"
                    file = File()
                    file.file.save(unique_filename, ContentFile(f.read()))
                    task = docx2html_task.delay(file.id)
                    task_ids.append(task.id)

                else:
                    return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            return Response(data=task_ids, status=status.HTTP_202_ACCEPTED)

        return Response(data={"error": "File does not exist"}, status=status.HTTP_400_BAD_REQUEST)

