from django.urls import path
from . import views

app_name = 'highlights'

urlpatterns = [
    path('upload/<int:match_id>/', views.upload_highlight, name='upload'),
    path('verification-queue/', views.verification_queue, name='verification_queue'),
    path('verify/<int:highlight_id>/', views.verify_highlight, name='verify'),
    path('gallery/', views.public_highlights, name='gallery'),
]
