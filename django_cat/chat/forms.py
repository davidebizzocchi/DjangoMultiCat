from django import forms
from library.models import Library

class ChatCreateForm(forms.Form):
    libraries = forms.ModelMultipleChoiceField(
        queryset=None,
        widget=forms.CheckboxSelectMultiple,
        required=False
    )

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['libraries'].queryset = Library.objects.filter(user=user)
