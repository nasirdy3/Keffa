from django.urls import path
from . import views

app_name = 'players'

urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('dashboard/', views.player_dashboard, name='player_dashboard'),
    path('profile/<int:player_id>/', views.player_profile, name='player_profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
]

