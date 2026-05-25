from django.urls import path
from . import views

urlpatterns = [
    path('', views.ranking_view, name='ranking'),
    path('profil/<str:username>/', views.profil_view, name='profil'),
]