"""
URL configuration for kefa_project project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponse
from django.views.decorators.cache import cache_control
from django.views.decorators.http import require_GET
from django.contrib.staticfiles.finders import find
from . import views

# --- PWA Helper Views ---
# These serve the static files from the root URL so the Service Worker has the correct scope

@require_GET
@cache_control(max_age=60 * 60, immutable=True, public=True) # Cache for 1 hour
def serve_service_worker(request):
    absolute_path = find('service-worker.js')
    if not absolute_path:
        return HttpResponse("Service Worker not found", status=404)
    with open(absolute_path, 'rb') as f:
        return HttpResponse(f.read(), content_type="application/javascript")

@require_GET
@cache_control(max_age=60 * 60 * 24, immutable=True, public=True) # Cache for 24 hours
def serve_manifest(request):
    absolute_path = find('manifest.json')
    if not absolute_path:
        return HttpResponse("Manifest not found", status=404)
    with open(absolute_path, 'rb') as f:
        return HttpResponse(f.read(), content_type="application/manifest+json")

urlpatterns = [
    # PWA Root Urls (Must be before admin to avoid conflict)
    path('service-worker.js', serve_service_worker, name='service_worker'),
    path('manifest.json', serve_manifest, name='manifest'),

    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('leaderboards/', views.leaderboards, name='leaderboards'),
    
    # New Information Suite
    path('', include('kefa_project.pages.urls')),
    
    # App URLs
    path('players/', include('kefa_project.players.urls')),
    path('tournaments/', include('kefa_project.tournaments.urls')),
    path('matches/', include('kefa_project.matches.urls')),
    path('highlights/', include('kefa_project.highlights.urls')),
    path('payments/', include('kefa_project.payments.urls')),
    path('teams/', include('kefa_project.teams.urls')),
    path('chat/', include('kefa_project.chat.urls')),
    path('notifications/', include('kefa_project.notifications.urls')),
    path('achievements/', include('kefa_project.achievements.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

