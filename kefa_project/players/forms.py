from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Player

class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user


class PlayerProfileForm(forms.ModelForm):
    class Meta:
        model = Player
        fields = ['full_name', 'efootball_id', 'address', 'phone_number', 'device_type', 'profile_picture', 'bio']
        widgets = {
            'address': forms.Textarea(attrs={'rows': 3}),
            'bio': forms.Textarea(attrs={'rows': 4}),
        }
