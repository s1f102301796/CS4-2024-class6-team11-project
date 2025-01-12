from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    games_played = models.IntegerField(default=0)
    games_won = models.IntegerField(default=0)

    @property
    def win_rate(self):
        return (self.games_won / self.games_played * 100) if self.games_played > 0 else 0
