from django.urls import path
from . import views

app_name = 'tournaments'

urlpatterns = [
    path('', views.tournaments_list, name='list'),
    path('<int:tournament_id>/', views.tournament_detail, name='detail'),
    path('<int:tournament_id>/standings/', views.tournament_standings, name='standings'),
    path('<int:tournament_id>/fixtures/', views.tournament_fixtures, name='fixtures'),
    path('<int:tournament_id>/top-scorers/', views.tournament_top_scorers, name='top_scorers'),
    path('<int:tournament_id>/finalize/', views.finalize_tournament, name='finalize'),
]
