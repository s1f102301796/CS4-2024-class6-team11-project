from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),  # メニュー画面
    path('othello/', views.othello_game, name='othello_game'),  # ゲーム画面
    path('join_queue/', views.join_queue, name='join_queue'),  # ランダムマッチングAPI
    path('<str:room_name>/', views.othello_room, name='othello_room'),  # 指定ルームに接続
    path('place_disc/<int:row>/<int:col>/', views.place_disc, name='place_disc'),  # 石を置く処理
    path('get_board/', views.get_board, name='get_board'),  # ボード情報を取得
]
