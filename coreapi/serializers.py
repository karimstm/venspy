from rest_framework import serializers
from .models import Upload, Project, Result, TypeUpload


class FileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Upload
        fields = '__all__'


class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = '__all__'

class ResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = Result
        fields = ['id', 'dateCreation', 'status']

class TypeUploadSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = TypeUpload
        fields = '__all__'
