from django.urls import path, include
from . import views
from rest_framework import routers

router = routers.DefaultRouter()
router.register('project', views.ProjectView)

urlpatterns = [
    path('', views.UploadView.as_view()),
    path('', include(router.urls))
]
