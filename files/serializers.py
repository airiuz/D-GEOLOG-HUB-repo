from rest_framework import serializers

from files.models import File


class Pdf2HtmlSerializer(serializers.Serializer):
    file = serializers.FileField()

    def validate_file(self, file):
        allowed_types = [
            'application/pdf'
        ]
        if file.content_type not in allowed_types:
            raise serializers.ValidationError("Only PDF file is allowed.")

        return file


class Pdf2DocxSerializer(serializers.Serializer):
    file = serializers.FileField()

    def validate_file(self, file):
        allowed_types = [
            'application/pdf'
        ]
        if file.content_type not in allowed_types:
            raise serializers.ValidationError("Only PDF file is allowed.")

        return file

class Docx2HtmlSerializer(serializers.Serializer):
    file = serializers.FileField()

    def validate_file(self, file):
        allowed_types = [
            'application/docx'
        ]
        if file.content_type not in allowed_types:
            raise serializers.ValidationError("Only Docx file is allowed.")

        return file


class Json2HtmlSerializer(serializers.Serializer):
    file = serializers.FileField()

    def validate_file(self, file):
        allowed_types = [
            'application/json'
        ]
        if file.content_type not in allowed_types:
            raise serializers.ValidationError("Only JSON file is allowed.")

        return file


class Json2DocxSerializer(serializers.Serializer):
    file = serializers.FileField()

    def validate_file(self, file):
        allowed_types = [
            'application/json'
        ]
        if file.content_type not in allowed_types:
            raise serializers.ValidationError("Only JSON file is allowed.")

        return file


class Docx2HtmlSerializer(serializers.Serializer):
    file = serializers.FileField()

    def validate_file(self, file):
        allowed_types = [
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        ]
        if file.content_type not in allowed_types:
            raise serializers.ValidationError("Only DOCX file is allowed.")

        return file
