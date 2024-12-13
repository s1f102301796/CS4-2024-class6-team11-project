from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),  # メニュー画面
    path('othello/', views.othello_game, name='othello_game'),  # ゲーム画面
    path('place_disc/<int:row>/<int:col>/', views.place_disc, name='place_disc'),  # 石を置く処理
    path('get_board/', views.get_board, name='get_board'),  # ボード情報を取得
    path('game/<int:game_id>/', views.othello_game_view, name='othello_game'), # ゲームの結果を表示
]
