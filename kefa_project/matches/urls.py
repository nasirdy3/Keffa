from django.urls import path
from . import views

app_name = 'matches'

urlpatterns = [
    path('<int:match_id>/ready/', views.match_ready, name='ready'),
    path('<int:match_id>/finished/', views.match_finished, name='finished'),
    path('<int:match_id>/postpone/', views.request_postponement, name='postpone'),
    path('postponement/<int:postponement_id>/accept/', views.accept_postponement, name='accept_postponement'),
    path('postponement/queue/', views.postponement_approval_queue, name='postponement_queue'),
    path('postponement/<int:postponement_id>/approve/', views.approve_postponement, name='approve_postponement'),
    path('friendly/create/', views.create_friendly_match, name='create_friendly'),
    path('friendly/<int:friendly_id>/accept/', views.accept_friendly_match, name='accept_friendly'),
    path('verification-queue/', views.verification_queue, name='verification_queue'),
    path('verify/<int:match_id>/', views.verify_match_result, name='verify_result'),
    path('<int:match_id>/', views.match_detail, name='detail'),
]

