from django.contrib import admin
from .models import Upload, Project, TypeUpload, Result

admin.site.register(Upload)
admin.site.register(Project)
admin.site.register(TypeUpload)
admin.site.register(Result)