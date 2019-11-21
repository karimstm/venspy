from rest_framework import serializers
from .models import Upload, Project, Result, TypeUpload





class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = '__all__'

class ResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = Result
        fields = ['id', 'dateCreation', 'status', 'description', 'warning']

class TypeUploadSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = TypeUpload
        fields = '__all__'

class FileSerializer(serializers.ModelSerializer):

    file_extension = serializers.SerializerMethodField('get_file_extension')

    class Meta:
        model = Upload
        fields = '__all__'

    def get_file_extension(self, queryset):
        result = TypeUpload.objects.get(id=queryset.typefile.id)
        serializer = TypeUploadSerializer(result, many=False)
        return serializer.data['name']
        