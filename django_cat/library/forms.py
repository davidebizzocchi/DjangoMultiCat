from django import forms
from library.models import Library

class LibraryForm(forms.ModelForm):
    class Meta:
        model = Library
        fields = ['name']
