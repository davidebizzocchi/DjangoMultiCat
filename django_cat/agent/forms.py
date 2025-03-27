from django import forms
import json
from agent.models import Agent, validate_capabilities

from django.conf import settings


class AgentForm(forms.ModelForm):
    capabilities = forms.MultipleChoiceField(
        choices=[ (capability, capability)
            for capability in settings.CAPABILITIES_TO_PLUGINS.keys()
        ],
        required=False,
        validators=[validate_capabilities]
    )

    class Meta:
        model = Agent
        fields = ['name', 'instructions', 'metadata', 'capabilities']
        widgets = {
            'metadata': forms.Textarea(attrs={
                'rows': 4, 
                'placeholder': '{"key": "value"}'
            }),
            'instructions': forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, user=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        self.fields['metadata'].required = False

    def clean_metadata(self):
        metadata = self.cleaned_data.get("metadata", "{}")
        
        if not metadata:
            return {}

        try:
            if isinstance(metadata, str):
                metadata = json.loads(metadata)
            if not isinstance(metadata, dict):
                raise forms.ValidationError("Metadata must be a valid JSON object")
            return metadata
        except json.JSONDecodeError:
            raise forms.ValidationError("Invalid JSON. Please check the syntax")

    def save(self, commit=True):
        agent = super().save(commit=False)
        agent.user = self.user
        
        if commit:
            agent.save()
        
        return agent