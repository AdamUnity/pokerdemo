from django.urls import path
from . import views

urlpatterns = [
    path('', views.lobby_view, name='lobby'),
    path('stworz/', views.stworz_pokoj, name='stworz'),
    path('dolacz/', views.dolacz_do_pokoju, name='dolacz'),
    path('pokoj/<str:kod>/', views.pokoj_view, name='pokoj'),
]