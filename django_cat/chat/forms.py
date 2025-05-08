from django import forms
from agent.models import Agent
from library.models import Library

from icecream import ic


class ChatCreateForm(forms.Form):
    agent = forms.ChoiceField(
        choices=[],
        widget=forms.Select(attrs={'class': 'form-select custom-option'}),
        label="Agent",
        required=True,
    )

    libraries = forms.MultipleChoiceField(
        choices=[],
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        required=False,
        label="Libraries"
    )

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['agent'].choices = [("default", "Default")] + [
            (agent.agent_id, agent.name) for agent in Agent.objects.filter(user=user).only("agent_id", "name")
        ]

        self.fields['libraries'].choices = [
            (library.library_id, library.name) for library in Library.objects.only("library_id", "name").filter(user=user)
        ]
