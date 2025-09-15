import os
import uuid

from django.core.exceptions import ValidationError
from django.db import models
from django.utils.deconstruct import deconstructible

@deconstructible
class FileExtensionValidator:
    def __init__(self, allowed_extensions):
        self.allowed_extensions = allowed_extensions

    def __call__(self, value):
        ext = os.path.splitext(value.name)[1]
        if not ext.lower() in self.allowed_extensions:
            raise ValidationError(f'Unsupported file extension. Only {", ".join(self.allowed_extensions)} are allowed.')




class File(models.Model):
    id = models.CharField(
        max_length=36,
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        unique=True
    )
    file = models.FileField(upload_to="private/files/", verbose_name="Upload file", validators=[FileExtensionValidator(['.json', '.docx', '.pdf'])])
    uploaded_at = models.DateTimeField(auto_now_add=True)




    class Meta:
        verbose_name = "File"
        verbose_name_plural = "Files"