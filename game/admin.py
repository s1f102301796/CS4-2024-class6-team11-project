from django.contrib import admin
from .models import Othello

# Register your models here.

@admin.register(Othello)
class OthelloAdmin(admin.ModelAdmin):
    list_display = ('id', 'current_turn', 'winner', 'created_at')
