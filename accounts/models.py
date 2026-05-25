from django.contrib.auth.models import AbstractUser
from django.db import models

class Player(AbstractUser):
    points = models.IntegerField(default=1000)

    groups = models.ManyToManyField(
        'auth.Group',
        blank=True,
        related_name='player_set'
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        blank=True,
        related_name='player_set'
    )