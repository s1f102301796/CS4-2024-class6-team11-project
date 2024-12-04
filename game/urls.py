from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('place_disc/<int:row>/<int:col>/', views.place_disc, name='place_disc'),
    path('othello/', views.othello_game, name='othello_game'),
]
