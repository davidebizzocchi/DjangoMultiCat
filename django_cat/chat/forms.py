from django import forms
from library.models import Library

class ChatCreateForm(forms.Form):
    libraries = forms.MultipleChoiceField(
        choices=[],
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        required=False,
        label="Libraries"
    )

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['libraries'].choices =[
            (library.library_id, library.name) for library in Library.objects.only("library_id", "name").filter(user=user)
        ]
