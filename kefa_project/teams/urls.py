from django.urls import path
from . import views

app_name = 'teams'

urlpatterns = [
    path('<int:team_id>/', views.team_profile, name='profile'),
]
