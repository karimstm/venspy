from django.urls import re_path
from .SocketHandler import SocketHandler

websocket_urlpatterns = [
    re_path(r'sockethandler/(?P<room_name>\w+)/$', SocketHandler),
]