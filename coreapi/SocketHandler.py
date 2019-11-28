from channels.generic.websocket import WebsocketConsumer
from .ThreadQueue import ThreadQueue
import json

threadHandler = None
clients = {}

class SocketHandler(WebsocketConsumer):

    def connect(self):
        self.accept()
        clients[self.scope['url_route']['kwargs']['room_name']] = self.send

    def disconnect(self, close_code):
        pass

    def receive(self, text_data):
        global threadHandler
        if not threadHandler:
            threadHandler = ThreadQueue(1)
        text_data_json = json.loads(text_data)
        threadHandler.addTask({
            "data":text_data_json, 
            "callBack": {
                "clients": clients, 
                "user": self.scope['url_route']['kwargs']['room_name']
                }
            })