from django.contrib import admin

from files.models import File


# Register your models here.


class FilesAdmin(admin.ModelAdmin):
    list_display = ('id', 'file', 'uploaded_at')
    exclude = ('generated_file',)




admin.site.register(File, FilesAdmin)
