from django.contrib import admin
from .models import Upload, Project, TypeUpload

admin.site.register(Upload)
admin.site.register(Project)
admin.site.register(TypeUpload)