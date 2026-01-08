from django import forms

class ContactForm(forms.Form):
    """
    Server-side validation for the contact page.
    """
    name = forms.CharField(
        max_length=100, 
        widget=forms.TextInput(attrs={
            'class': 'form-control', 
            'placeholder': 'Your Name'
        })
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control', 
            'placeholder': 'Your Email'
        })
    )
    subject = forms.CharField(
        max_length=200, 
        widget=forms.TextInput(attrs={
            'class': 'form-control', 
            'placeholder': 'Topic'
        })
    )
    message = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control', 
            'placeholder': 'How can we help you?',
            'rows': 5
        })
    )
