from rest_framework import serializers
from .models import Upload, Project


class FileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Upload
        fields = '__all__'


class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = '__all__'
