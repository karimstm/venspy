from rest_framework.parsers import FileUploadParser
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status, viewsets
import os

from .serializers import FileSerializer, ProjectSerializer
from .models import Upload, Project


class ProjectView(viewsets.ModelViewSet):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer


def handle_upload_file(f, path):
    with open(path, 'wb+') as destination:
        for chunk in f.chunks():
            destination.write(chunk)


class UploadView(APIView):
    parser_class = (FileUploadParser,)

    def post(self, request, *args, **kwargs):
        path = "./media/" + str(Project.objects.all()
                                [int(request.data['project']) - 1]) + '/' + str(request.data['file'])
        file_serializer = FileSerializer(data=request.data)
        if (os.path.exists('./media/') == False):
            os.mkdir('./media/')
        if (os.path.exists("./media/" + str(Project.objects.all()[int(request.data['project']) - 1])) == False):
            os.mkdir("./media/" + str(Project.objects.all()
                                      [int(request.data['project']) - 1]) + '/')
        if file_serializer.is_valid():
            handle_upload_file(request.data['file'], path)
            file_serializer.save(file=path)
            return Response(file_serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(file_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
