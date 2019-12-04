from .serializers import FileSerializer, ProjectSerializer, SettingSerializer, ResultSerializer, TypeUploadSerializer
from .models import Upload, Project, Result, Upload, TypeUpload, Settings
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.parsers import FileUploadParser
from rest_framework.response import Response
from rest_framework import status, viewsets
from rest_framework.views import APIView
from rest_framework import generics
from rest_framework import filters
#from .SocketHandler import clients
from .static import threadHandler
from .Simulator import Simulator
from datetime import datetime
from pathlib import Path
import win32com.client
import getpass
import ntpath
import json
import time
import os

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
    parser_class = (FileUploadParser,)
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['typefile']

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
        if os.path.exists(str(instance.file)):
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
        print(request.data)
        try:
            project_instance = Project.objects.get(id=request.data['project'])
            typefile_instance = TypeUpload.objects.get(
                id=request.data['typefile'])
        except:
            return Response(data={"msg": "missing_data"}, status=status.HTTP_400_BAD_REQUEST)
        if Upload.objects.filter(project=Project.objects.get(id=request.data['project']), name=request.data['file'].name).count() == 0:
            request.data['name'] = request.data['file'].name
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            self.handle_upload_file(request.data['file'], path)
            self.perform_create(serializer, BASE_DIR, path2)
            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
        else:
            file_instance = Upload.objects.get(
                project=project_instance, name=request.data['file'].name)
            file_instance.dateCreation = datetime.now()
            file_instance.file = BASE_DIR + path2
            file_instance.name = ntpath.basename(request.data['file'].name)
            file_instance.typefile = typefile_instance
            file_instance.save()
            return Response(data={"msg": "File Updated"}, status=status.HTTP_201_CREATED)

    def perform_update(self, serializer, BASE_DIR, path2):
        serializer.save(file=BASE_DIR + path2)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        path, path2 = self.path_maker(request)
        request.data['name'] = request.data['file'].name
        serializer = self.get_serializer(
            instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.handle_upload_file(request.data['file'], path)
        self.perform_update(serializer, BASE_DIR, path2)

        if getattr(instance, '_prefetched_objects_cache', None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}

        return Response(serializer.data)


class UrlFilter:
    def __init__(self, options, params):
        self.params = params
        #self.params.update(options[0])
        #del options[0]
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

    def execute(self, callBack=None):
        if self.delegator:
            return self.delegator(callBack)
        return 'Error Handling'


class SimulationsHandler(UrlFilter):
    def __init__(self, params):
        options = [
        {
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
            'description': 'default',
            'func': self.generate
        }]
        super().__init__(options, params)

    def getResults(self, callBack):
        queryset = Result.objects.filter(project__pk=self.params.get('pk'))\
            .order_by('-dateCreation')
        serializer = ResultSerializer(queryset, many=True)
        return serializer.data

    def getResult(self, callBack):
        queryset = Result.objects.get(
            project__pk=self.params.get('pk'), pk=self.params.get('id'))
        if not queryset.status:
            return ({'status': 'in queue'})
        data = Path(queryset.path).read_bytes()
        data = json.loads(data)
        if not self.params.get('var'):
            return data
        for var in self.params.get('var').split(','):
            if var not in data.keys():
                return list(data.keys())
        results = {}
        for var in self.params.get('var').split(','):
            results[var] = data[var]
        return results

    def generate(self, callBack):
        threadHandler.addTask(SimulationsHandler.simulate, self.params, callBack)
        return {"status": "pending"}

    @staticmethod
    def simulate(params, callBack):
        print("start")
        pk = params.get('pk')
        description = params.get('description')
        project = Project.objects.get(id=pk)
        project.runs = project.runs + 1
        project.save()
        model = Upload.objects.filter(project=pk, typefile__name="mdl")
        if not model:
            status = {"status": "failed", "message": F"you must load model"}
            if callBack:
                callBack["clients"][callBack["user"]](json.dumps(status))
            return status
        result = Result.objects.create(status=False, project=project, description=description, warning='')
        BASE_DIR = F"{os.path.dirname(os.path.dirname(os.path.abspath(__file__)))}/media/{pk}"
        simulator = Simulator('"D:/Vensim/vendss64.exe"', model[0], runname=F"{BASE_DIR}/{result.id}", handlerFile=F"{BASE_DIR}/{result.id}")
        jsonFile = F"{BASE_DIR}/result{result.id}.json"
        Path(jsonFile).write_text(json.dumps(simulator.results))
        try:
            error_path = Settings.objects.get(name='error_path').path
        except:
            print("error_path does not exist in settings")
            error_path = os.path.join('C:\\Users\\', getpass.getuser(
            ), 'AppData\\Roaming\\Vensim\\vensimdp.err')
        warning = Get_Warnings(error_path)
        result.path = jsonFile
        result.status = True
        result.warning = warning
        result.save()
        if callBack:
            callBack["clients"][callBack["user"]](json.dumps({
                "pk": pk, 
                'id': result.id, 
                "status": "success", 
                "message": F"simulation {result.id} complete"
                }))


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
        #simulationsHandler = SimulationsHandler(pk, request.query_params)
        #response = simulationsHandler.execute()
        params = request.query_params.copy()
        params["pk"] = pk
        response = SimulationsHandler(params).execute()
        return Response(response)


class SettingsView(generics.ListCreateAPIView):
    serializer_class = SettingSerializer
    queryset = Settings.objects.all()
