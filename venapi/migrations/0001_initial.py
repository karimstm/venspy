# Generated by Django 2.2.5 on 2019-10-09 14:05

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Project',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50)),
                ('description', models.CharField(max_length=255)),
                ('creation_date', models.DateTimeField(auto_now=True)),
                ('modification_date', models.DateTimeField(auto_now=True)),
                ('runs', models.IntegerField()),
            ],
        ),
        migrations.CreateModel(
            name='Upload',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('file', models.FileField(max_length=255, upload_to='media/')),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='venapi.Project')),
            ],
        ),
    ]
