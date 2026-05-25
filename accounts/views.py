from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from .forms import RegisterForm

def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            player = form.save()
            login(request, player)
            return redirect('index')
    else:
        form = RegisterForm()
    return render(request, 'accounts/register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        player = authenticate(request, username=username, password=password)
        if player is not None:
            login(request, player, backend='django.contrib.auth.backends.ModelBackend')
            return redirect('index')
        else:
            return render(request, 'accounts/login.html', {'error': 'Błędny login lub hasło'})
    return render(request, 'accounts/login.html')

def logout_view(request):
    logout(request)
    return redirect('login')