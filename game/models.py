from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class MatchmakingQueue(models.Model):
    user = models.OneToOneField(
        get_user_model(), on_delete=models.CASCADE, related_name="queue"
    )
    joined_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} joined at {self.joined_at}"


# オセロクラス
class Othello(models.Model):
    room_name = models.CharField(max_length=255, unique=True)
    player_black = models.ForeignKey(
        User,
        related_name="games_as_black",
        on_delete=models.CASCADE,
        null=True,  # 試合中の空席を許可
        blank=True
    )
    player_white = models.ForeignKey(
        User,
        related_name="games_as_white",
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    black_score = models.IntegerField(default=0)
    white_score = models.IntegerField(default=0)
    board = models.JSONField(default=list)
    current_turn = models.CharField(
        max_length=5,
        choices=[("black", "Black"), ("white", "White")],
        default="black",
    )
    winner = models.CharField(
        max_length=5,
        choices=[("black", "Black"), ("white", "White"), ("draw", "Draw")],
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    placeable_positions = models.JSONField(default=list)

    # オセロの移動方向リスト（共通化）
    DIRECTIONS = [
        (-1, 0), (1, 0), (0, -1), (0, 1),
        (-1, -1), (-1, 1), (1, -1), (1, 1)
    ]

    def initialize_board(self):
        # オセロの初期盤面設定
        self.board = [[None] * 8 for _ in range(8)]
        self.board[3][3] = self.board[4][4] = "white"
        self.board[3][4] = self.board[4][3] = "black"
        self.current_turn = "black"
        self.placeable_positions = []
        self.get_placeable_positions()
        self.winner = None  # 勝者データもリセット
        self.save()


    def is_valid_position(self, x, y):
        # ボード内の有効な座標か判定
        return 0 <= x < 8 and 0 <= y < 8


    def can_place(self, x, y):
        # 指定位置に駒を置けるか判定
        if self.board[x][y] is not None:
            return False

        opponent = "black" if self.current_turn == "white" else "white"
        for dx, dy in self.DIRECTIONS:
            nx, ny = x + dx, y + dy
            found_opponent = False

            while self.is_valid_position(nx, ny) and self.board[nx][ny] == opponent:
                found_opponent = True
                nx += dx
                ny += dy

            if found_opponent and self.is_valid_position(nx, ny) and self.board[nx][ny] == self.current_turn:
                return True

        return False
    

    def get_placeable_positions(self):
        positions = []
        self.placeable_positions.clear()
        for row in range(8):
            for col in range(8):
                if self.can_place(row, col):
                    positions.append((row, col))

        self.placeable_positions = positions
        return True


    def flip_discs(self, x, y):
        # 指定位置で駒を裏返す
        opponent = "black" if self.current_turn == "white" else "white"

        for dx, dy in self.DIRECTIONS:
            nx, ny = x + dx, y + dy
            discs_to_flip = []

            while self.is_valid_position(nx, ny) and self.board[nx][ny] == opponent:
                discs_to_flip.append((nx, ny))
                nx += dx
                ny += dy

            if self.is_valid_position(nx, ny) and self.board[nx][ny] == self.current_turn:
                for fx, fy in discs_to_flip:
                    self.board[fx][fy] = self.current_turn

        self.board[x][y] = self.current_turn
        self.save()


    def switch_turn(self):
        self.current_turn = "white" if self.current_turn == "black" else "black"
        if not self.can_any_player_move():
            print(f"No valid moves for {self.current_turn}. Switching turn again.")
            self.current_turn = "white" if self.current_turn == "black" else "black"
            if not self.can_any_player_move():
                print("No valid moves for both players. Ending the game.")
                self.check_game_over()
        self.save()  # 状態を保存



    def can_any_player_move(self):
        for x in range(8):
            for y in range(8):
                if self.can_place(x, y):
                    print(f"Player {self.current_turn} can place at ({x}, {y})")
                    return True
        print(f"Player {self.current_turn} has no valid moves.")
        return False
    

    def can_any_player_move_for(self, player_color):
        original_turn = self.current_turn
        self.current_turn = player_color
        can_move = any(
            self.can_place(row, col) for row in range(8) for col in range(8)
        )
        self.current_turn = original_turn
        return can_move



    def update_player_stats(self):
        """プレイヤーの統計情報を更新する"""
        if self.player_black:
            self.player_black.games_played += 1
        if self.player_white:
            self.player_white.games_played += 1

        if self.winner == "black" and self.player_black:
            self.player_black.games_won += 1
        elif self.winner == "white" and self.player_white:
            self.player_white.games_won += 1

        if self.player_black:
            self.player_black.save()
        if self.player_white:
            self.player_white.save()


    def check_game_over(self):
        black_count = sum(row.count("black") for row in self.board)
        white_count = sum(row.count("white") for row in self.board)
        board_full = black_count + white_count == 64

        no_moves_for_black = not self.can_any_player_move_for("black")
        no_moves_for_white = not self.can_any_player_move_for("white")
        both_cannot_move = no_moves_for_black and no_moves_for_white

        if board_full or both_cannot_move:
            self.black_score = black_count
            self.white_score = white_count

            if black_count > white_count:
                self.winner = "black"
            elif white_count > black_count:
                self.winner = "white"
            else:
                self.winner = "draw"

            self.update_player_stats()  # プレイヤー情報を更新
            self.save()
            print(f"Game over. Winner: {self.winner}")
        else:
            print("Game not over yet.")



    def place_disc(self, x, y):
        # 指定位置に駒を置く
        if not self.is_valid_position(x, y):
            return "Invalid position!"
        if self.board[x][y] is not None:
            return "Invalid position! Cell already occupied."
        if not self.can_place(x, y):
            return "Invalid move! Cannot place here."

        self.flip_discs(x, y)
        self.switch_turn()
        self.get_placeable_positions()
        if not self.placeable_positions:
            self.switch_turn()
            self.get_placeable_positions()
        self.check_game_over()
        self.save()  # 状態を保存
        return "Disc placed successfully."


    def __str__(self):
        return f"Othello Game - Current Turn: {self.current_turn}"
