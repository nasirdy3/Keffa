from django.urls import path
from . import views

# This namespace is used as 'players:name' in templates
app_name = 'players'

urlpatterns = [
    path('register/', views.register, name='register'),
    # Changed name from 'login' to 'user_login' to match base.html usage
    path('login/', views.user_login, name='user_login'),
    # Changed name from 'logout' to 'user_logout' to match base.html usage
    path('logout/', views.user_logout, name='user_logout'),
    path('dashboard/', views.player_dashboard, name='player_dashboard'),
    path('profile/<int:player_id>/', views.player_profile, name='player_profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
]

