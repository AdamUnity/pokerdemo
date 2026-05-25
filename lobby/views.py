from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from accounts.models import Player
from .models import Room
import random
import string

def generuj_kod():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

@login_required
def lobby_view(request):
    pokoj = Room.objects.filter(gracze=request.user, aktywna=True).first()
    return render(request, 'lobby/lobby.html', {'pokoj': pokoj})

@login_required
def stworz_pokoj(request):
    gracz = Player.objects.get(pk=request.user.pk)
    
    if request.method == 'POST':
        min_punkty = int(request.POST.get('min_punkty', 100))
        
        if gracz.points < min_punkty:
            return render(request, 'lobby/stworz.html', {
                'error': f'Potrzebujesz minimum {min_punkty} punktów żeby stworzyć ten pokój.'
            })

        kod = generuj_kod()
        while Room.objects.filter(kod=kod).exists():
            kod = generuj_kod()

        pokoj = Room.objects.create(
            kod=kod,
            host=gracz,
            min_punkty=min_punkty
        )
        pokoj.gracze.add(gracz)
        return redirect('pokoj', kod=pokoj.kod)
    
    return render(request, 'lobby/stworz.html')

@login_required
def dolacz_do_pokoju(request):
    gracz = Player.objects.get(pk=request.user.pk)
    
    if request.method == 'POST':
        kod = request.POST.get('kod', '').upper()
        
        try:
            pokoj = Room.objects.get(kod=kod, aktywna=True)
        except Room.DoesNotExist:
            return render(request, 'lobby/dolacz.html', {
                'error': 'Nie znaleziono pokoju o tym kodzie.'
            })

        if pokoj.czy_pelny():
            return render(request, 'lobby/dolacz.html', {
                'error': 'Pokój jest pełny.'
            })

        if gracz.points < pokoj.min_punkty:
            return render(request, 'lobby/dolacz.html', {
                'error': f'Potrzebujesz minimum {pokoj.min_punkty} punktów żeby dołączyć.'
            })

        pokoj.gracze.add(gracz)
        return redirect('pokoj', kod=pokoj.kod)

    return render(request, 'lobby/dolacz.html')

@login_required
def pokoj_view(request, kod):
    pokoj = get_object_or_404(Room, kod=kod, aktywna=True)
    gracz = Player.objects.get(pk=request.user.pk)
    
    if gracz not in pokoj.gracze.all():
        return redirect('dolacz')
    
    return render(request, 'lobby/pokoj.html', {'pokoj': pokoj})