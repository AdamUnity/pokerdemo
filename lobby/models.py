from django.db import models
from accounts.models import Player
import json


class Room(models.Model):
    kod = models.CharField(max_length=6, unique=True)
    host = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='hosted_rooms')
    gracze = models.ManyToManyField(Player, related_name='rooms', blank=True)
    max_graczy = models.IntegerField(default=6)
    min_punkty = models.IntegerField(default=100)
    aktywna = models.BooleanField(default=True)
    stworzona = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Pokój {self.kod}'

    def czy_pelny(self):
        return self.gracze.count() >= self.max_graczy


class GameState(models.Model):
    pokoj = models.OneToOneField(Room, on_delete=models.CASCADE, related_name='game_state')
    stan_json = models.TextField()
    zaktualizowano = models.DateTimeField(auto_now=True)

    def get_stan(self):
        from .poker import GraPoker
        return GraPoker.ze_slownika(json.loads(self.stan_json))

    def set_stan(self, gra):
        self.stan_json = json.dumps(gra.do_slownika())
        self.save()

    def __str__(self):
        return f'Gra w pokoju {self.pokoj.kod}'