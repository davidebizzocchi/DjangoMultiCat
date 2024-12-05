from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import authenticate


class UserRegistrationForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username']

class LoginForm(AuthenticationForm):
    # Rimuoviamo il campo password
    password = None
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'password' in self.fields:
            del self.fields['password']
        self.fields['username'].widget.attrs.update({
            'placeholder': 'Inserisci username',
            'class': 'form-control'
        })
        
    def clean(self):
        username = self.cleaned_data.get('username')
        if username:
            self.user_cache = self.get_user()
        return self.cleaned_data

    def get_user(self):
        return authenticate(
            self.request,
            username=self.cleaned_data.get('username'),
            password=None
        )