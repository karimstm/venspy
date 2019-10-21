from rest_framework import serializers
from .models import Upload, Project, Result


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
