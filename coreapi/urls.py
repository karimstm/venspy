from django.urls import path, include
from . import views
from rest_framework import routers

router = routers.DefaultRouter()
router.register('', views.ProjectView)

urlpatterns = [
    path('', include(router.urls)),
    path('upload', views.UploadView.as_view()),
    path('simulations/<int:pk>/', views.SimulationsViewset.as_view())
]
