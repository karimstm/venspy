from rest_framework.parsers import FileUploadParser
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status, viewsets
import os
import pathlib
import json

from .serializers import FileSerializer, ProjectSerializer, ResultSerializer
from .models import Upload, Project, Result
from .library import venpylib as venpy
from background_task import background


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
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        media = './media/'
        media2 = '/media/'
        project_path = media + \
            str(request.data['project']) + '/'
        path = media + str(request.data['project']) + \
            '/' + str(request.data['file'])
        path2 = media2 + \
            str(request.data['project']) + '/' + str(request.data['file'])
        file_serializer = FileSerializer(data=request.data)
        if os.path.exists(media) == False:
            os.mkdir(media)
        if os.path.exists(project_path) == False:
            os.mkdir(project_path)
        if file_serializer.is_valid():
            handle_upload_file(request.data['file'], path)
            file_serializer.save(file=BASE_DIR + path2)
            return Response(file_serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(file_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

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
    model = Upload.objects.get(project=pk, typefile__name="vmpx")
    modelHandler = venpy.load(model.file)
    modelHandler.run()
    latest = len(Result.objects.all())
    jsonFile = F"{BASE_DIR}/result{latest + 1}.json"
    modelHandler.result().to_json(jsonFile)
    result = Result.objects.get(id=id)
    result.path = jsonFile
    result.status = True
    result.save()
    print(F"simulation of project {pk}, number {id} done.")

class SimulationsHandler(UrlFilter):
    def __init__(self, pk, params):
        options = [{
            '_pk': pk
            },{
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
            'func' : self.generate
            }]
        super().__init__(options, params)

    def getResults(self):
        queryset = Result.objects.filter(project__pk=self.params.get('_pk'))
        serializer = ResultSerializer(queryset, many=True)
        return serializer.data

    def getResult(self):
        queryset = Result.objects.get(project__pk=self.params.get('_pk'), pk=self.params.get('id'))
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
        result = Result(status=False, project=project)
        result.save()
        addToQueue(self.params.get('_pk'), result.id)
        return ({'status' : 'in queue', 'id': result.id})

class SimulationsViewset(APIView):
    def get(self, request, pk, format=None):
        simulationsHandler = SimulationsHandler(pk, request.query_params)
        response = simulationsHandler.execute()
        return Response(response)


