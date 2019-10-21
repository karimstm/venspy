from django.db import models


class Project(models.Model):
    name = models.CharField(max_length=50)
    description = models.CharField(max_length=255)
    creation_date = models.DateTimeField(auto_now=True)
    modification_date = models.DateTimeField(auto_now=True)
    runs = models.IntegerField()

    def __str__(self):
        return self.name


class TypeUpload(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name


class Upload(models.Model):
    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name='project_path')
    file = models.FileField(upload_to='media/', max_length=255)
    typefile = models.ForeignKey(
        TypeUpload, on_delete=models.CASCADE, related_name='type_file')

    def __str__(self):
        return self.file.name


class Result(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    path = models.CharField(max_length=100, null=True, blank=True)
    dateCreation = models.DateTimeField(auto_now=True)
    status = models.BooleanField(default=False)
