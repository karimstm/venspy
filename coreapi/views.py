from rest_framework.parsers import FileUploadParser
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status, viewsets
from rest_framework import generics
import os
import pathlib
import json
import getpass
import win32com.client
from rest_framework import filters
from .serializers import FileSerializer, ProjectSerializer, SettingSerializer, ResultSerializer, TypeUploadSerializer
from .models import Upload, Project, Result, Upload, TypeUpload, Settings
from .library import venpylib as venpy
from background_task import background
from django_filters.rest_framework import DjangoFilterBackend


class ProjectView(viewsets.ModelViewSet):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer


class ModelsView(generics.RetrieveAPIView):
    serializer_class = FileSerializer
    queryset = Upload.objects.all()

    def get(self, request, pk):
        project = Project.objects.get(id=pk)
        files = Upload.objects.filter(project=project)
        serializer = FileSerializer(files, many=True)
        return Response(serializer.data)


class TypeUploadView(viewsets.ModelViewSet):
    queryset = TypeUpload.objects.all()
    serializer_class = TypeUploadSerializer


class UploadView(viewsets.ModelViewSet):
    queryset = Upload.objects.all()
    serializer_class = FileSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['typefile']
    parser_class = (FileUploadParser,)

    def handle_upload_file(self, f, path):
        with open(path, 'wb+') as destination:
            for chunk in f.chunks():
                destination.write(chunk)

    def path_maker(self, request):
        media = './media/'
        media2 = '/media/'
        project_path = media + \
            str(request.data['project']) + '/'
        path = media + str(request.data['project']) + \
            '/' + str(request.data['file'])
        path2 = media2 + \
            str(request.data['project']) + '/' + str(request.data['file'])
        if os.path.exists(media) == False:
            os.mkdir(media)
        if os.path.exists(project_path) == False:
            os.mkdir(project_path)
        return path, path2

    def perform_destroy(self, instance):
        os.remove(str(instance.file))
        instance.delete()

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def perform_create(self, serializer, BASE_DIR, path2):
        serializer.save(file=BASE_DIR + path2)

    def create(self, request, *args, **kwargs):
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        path, path2 = self.path_maker(request)
        request.data['name'] = request.data['file'].name
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.handle_upload_file(request.data['file'], path)
        self.perform_create(serializer, BASE_DIR, path2)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class UrlFilter:
    def __init__(self, options, params):
        self.params = params.copy()
        self.params.update(options[0])
        del options[0]
        self.delegator = options[0]['func']
        self.__parse(options)

    def __check(self, option):
        for key in option.keys():
            if key == 'func':
                continue
            if key not in self.params.keys():
                return False
            if option[key] != 'default' and option[key] != self.params[key]:
                return False
        return True

    def __parse(self, options):
        for option in options:
            if self.__check(option):
                self.delegator = option['func']

    def execute(self):
        if self.delegator:
            return self.delegator()
        return 'Error Handling'


@background(schedule=0)
def addToQueue(pk, id):
    BASE_DIR = F"{os.path.dirname(os.path.dirname(os.path.abspath(__file__)))}/media/{pk}"
    model = Upload.objects.get(project=pk, typefile__name="vpmx")
    modelHandler = venpy.load(model.file)
    modelHandler.run()
    latest = len(Result.objects.all())
    jsonFile = F"{BASE_DIR}/result{latest + 1}.json"
    modelHandler.result().to_json(jsonFile)
    # Get errors
    try:
        error_path = Settings.objects.get(name='error_path').path
    except:
        print("error_path does not exist in settings")
        error_path = os.path.join('C:\\Users\\', getpass.getuser(
        ), 'AppData\\Roaming\\Vensim\\vensimdll.err')
    warning = Get_Warnings(error_path)
    result = Result.objects.get(id=id)
    result.path = jsonFile
    result.status = True
    result.warning = warning
    result.save()
    xl = win32com.client.Dispatch("Excel.Application")
    xl.DisplayAlerts = False
    xl.Quit()
    print(F"simulation of project {pk}, number {id} done.")


class SimulationsHandler(UrlFilter):
    def __init__(self, pk, params):
        options = [{
            '_pk': pk
        }, {
            '/': 'default',
            'func': self.getResults
        }, {
            'id': 'default',
            'func': self.getResult
        }, {
            'id': 'default',
            'var': 'default',
            'func': self.getResult
        }, {
            'option': 'generate',
            'func': self.generate
        }]
        super().__init__(options, params)

    def getResults(self):
        queryset = Result.objects.filter(project__pk=self.params.get('_pk'))\
            .order_by('-dateCreation')
        serializer = ResultSerializer(queryset, many=True)
        return serializer.data

    def getResult(self):
        queryset = Result.objects.get(
            project__pk=self.params.get('_pk'), pk=self.params.get('id'))
        if not queryset.status:
            return ({'status': 'in queue'})
        data = pathlib.Path(queryset.path).read_bytes()
        data = json.loads(data)
        if not self.params.get('var'):
            return data
        if self.params.get('var') not in data.keys():
            return list(data.keys())
        if self.params.get('var') in data.keys():
            return data[self.params.get('var')]
        return data

    def generate(self):
        project = Project.objects.get(id=self.params.get('_pk'))
        project.runs = project.runs + 1
        project.save()
        description = self.params.get('description')
        result = Result(status=False, project=project,
                        description=description, warning='')
        result.save()
        addToQueue(self.params.get('_pk'), result.id)
        return ({'status': 'in queue', 'id': result.id})


def Get_Warnings(path):
    print(path)
    if os.path.isfile(path):
        with open(path, 'r+') as content_file:
            content = content_file.read()
            content_file.truncate(0)
            return content
    return 'Warning path either does not exists or it\'s a directory'


class SimulationsViewset(APIView):

    def get(self, request, pk, format=None):
        simulationsHandler = SimulationsHandler(pk, request.query_params)
        response = simulationsHandler.execute()
        return Response(response)


class SettingsView(generics.ListCreateAPIView):
    serializer_class = SettingSerializer
    queryset = Settings.objects.all()
