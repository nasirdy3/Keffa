from django.shortcuts import render, redirect
from django.contrib import messages
from .models import FAQ
from .forms import ContactForm

def about(request):
    """Static About Page"""
    return render(request, 'pages/about.html')

def faq(request):
    """Dynamic FAQ Page fetching visible questions"""
    faqs = FAQ.objects.filter(is_visible=True)
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
