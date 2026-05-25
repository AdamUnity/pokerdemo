from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('main_page.urls')),
    path('accounts/', include('accounts.urls')),
    path('ranking/', include('ranking.urls')),
    path('lobby/', include('lobby.urls')),
]