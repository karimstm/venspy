from channels.generic.websocket import WebsocketConsumer
from .static import threadHandler
from .views import SimulationsHandler
import json

clients = {}

class SocketHandler(WebsocketConsumer):

    def connect(self):
        self.accept()
        clients[self.scope['url_route']['kwargs']['room_name']] = self.send

    def disconnect(self, close_code):
        pass

    def receive(self, text_data):
        global threadHandler
        text_data_json = json.loads(text_data)
        SimulationsHandler(text_data_json).execute({
                "clients": clients, 
                "user": self.scope['url_route']['kwargs']['room_name']
                })