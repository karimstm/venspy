from django.urls import path, include
from . import views
from rest_framework import routers
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

router = routers.DefaultRouter()
router.register(r'project', views.ProjectView)
router.register(r'types', views.TypeUploadView)
router.register(r'upload', views.UploadView)

urlpatterns = [
    path('', include(router.urls)),
    path('api/auth/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('project/<int:pk>/models', views.ModelsView.as_view()),
    path('simulations/<int:pk>/', views.SimulationsViewset.as_view()),
    path('settings/', views.SettingsView.as_view()),
    path('units/<int:pk>/', views.MdlTopJsonView.as_view()),
    path('getwarning/<int:pk>/<int:rpk>/', views.getWarningView.as_view())
]
