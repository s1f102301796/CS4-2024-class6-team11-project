# chess/routing.py
from django.urls import path
from . import consumers

websocket_urlpatterns = [
    path('ws/chess_app/', consumers.ChessConsumer.as_asgi()),
]
