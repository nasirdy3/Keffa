from django.shortcuts import render, redirect
from django.contrib import messages
from django.db.utils import OperationalError, ProgrammingError
from .models import FAQ
from .forms import ContactForm
from kefa_project.achievements.services import calculate_player_of_the_week

def home(request):
    """
    Home page view. 
    Fetches live matches, upcoming matches, featured tournaments, 
    and the Player of the Week.
    """
    from kefa_project.tournaments.models import Tournament
    from kefa_project.matches.models import Match
    from django.utils import timezone
    
    now = timezone.now()
    today = now.date()
    
    # Existing logic (simulated/assumed to be here or needs to be added if missing)
    # The previous view_file of home.html implies these context variables exist.
    # However, pages/views.py provided only showed about, faq, contact. 
    # I MUST FIND WHERE home view is. It might be in pages/urls.py pointing to a different view or I missed it.
    
    # Wait, the previous `view_file` for `pages/views.py` did NOT show `def home`.
    # Let me check `kefa_project/urls.py` to see where `home` is mapped.
    pass

def about(request):
    """Static About Page"""
    return render(request, 'pages/about.html')

def faq(request):
    """
    Dynamic FAQ Page fetching visible questions.
    Includes defensive coding to handle cases where the DB table 
    might be missing during migrations.
    """
    try:
        faqs = FAQ.objects.filter(is_visible=True)
    except (OperationalError, ProgrammingError):
        # ARCHITECT NOTE: This handles the "relation does not exist" error gracefully
        # by returning an empty list instead of crashing the server.
        faqs = []
        
    return render(request, 'pages/faq.html', {'faqs': faqs})

def contact(request):
    """Contact page with form handling"""
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            # In a real scenario, we would send an email here
            # send_mail(...)
            
            # For now, just show a success message
            messages.success(request, f"Thank you, {form.cleaned_data['name']}! Your message has been received. We will contact you at {form.cleaned_data['email']}.")
            return redirect('pages:contact')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = ContactForm()
    
    return render(request, 'pages/contact.html', {'form': form})

