from django.urls import path, include
from . import views
from rest_framework import routers

router = routers.DefaultRouter()
router.register(r'project', views.ProjectView)
router.register(r'types', views.TypeUploadView)

urlpatterns = [
    path('', include(router.urls)),
    path('project/<int:pk>/models', views.ModelsView.as_view()),
    path('upload', views.UploadView.as_view()),
    path('simulations/<int:pk>/', views.SimulationsViewset.as_view()),
]
