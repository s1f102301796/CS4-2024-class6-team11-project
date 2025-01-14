# chess/routing.py
from django.urls import path
from . import consumers

websocket_urlpatterns = [
    path('ws/chess/', consumers.ChessConsumer.as_asgi()),
]
