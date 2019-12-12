from django.db import models
from django.contrib.auth.models import User

TYPECHOICES = [
    ('vpmx', 'VPMX'),
    ('xlsx', 'EXCEL'),
    ('mdl', 'MDL')
]


class Project(models.Model):
    name = models.CharField(max_length=50)
    description = models.CharField(max_length=255)
    creation_date = models.DateTimeField(auto_now=True)
    modification_date = models.DateTimeField(auto_now=True)
    runs = models.IntegerField(default=0)

    def __str__(self):
        return self.name


class TypeUpload(models.Model):
    name = models.CharField(max_length=50, default='model',
                            choices=TYPECHOICES, unique=True)

    def __str__(self):
        return self.name


class Upload(models.Model):
    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name='project_path')
    file = models.FileField(upload_to='media/', max_length=255)
    name = models.CharField(max_length=255)
    dateCreation = models.DateTimeField(auto_now=True)
    typefile = models.ForeignKey(
        TypeUpload, on_delete=models.CASCADE, related_name='type_file')

    def __str__(self):
        return self.file.name


class Result(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    path = models.CharField(max_length=100, null=True, blank=True)
    dateCreation = models.DateTimeField(auto_now=True)
    status = models.BooleanField(default=False)
    description = models.TextField(null=True, blank=True)
    warning = models.TextField(null=True, blank=True)


class Entity(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    users = models.ManyToManyField(User)

# Settings table
class Settings(models.Model):
    name = models.CharField(max_length=100, unique=True)
    path = models.TextField()
