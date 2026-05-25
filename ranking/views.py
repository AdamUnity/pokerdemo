from django.shortcuts import render, get_object_or_404
from accounts.models import Player

def ranking_view(request):
    players = Player.objects.order_by('-points')
    return render(request, 'ranking/ranking.html', {'players': players})

def profil_view(request, username):
    player = get_object_or_404(Player, username=username)
    pozycja = Player.objects.filter(points__gt=player.points).count() + 1
    return render(request, 'ranking/profil.html', {'player': player, 'pozycja': pozycja})