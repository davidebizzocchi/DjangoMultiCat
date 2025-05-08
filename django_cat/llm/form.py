from common.form_pydantic import PydanticFormBuilder

from users.models import UserProfile
from llm.models import LLM

from django import forms

class Forms:
    def __init__(self, user: UserProfile, llm: LLM = None, **kwargs):
        self.user = user
        self.llm = llm
        self.llm_base = llm.name if llm else None
        self.initial = kwargs.get("initial", {})

        self.forms = {
            title: {
                "name": schema["humanReadableName"],
                "form": PydanticFormBuilder.create_form_from_schema(schema, title)(initial=(self.get_initial() if title == self.llm_base else {})),
            }
            for title, schema in LLM.get_llm_schemas(user).items()
        }

class LLMForm(forms.ModelForm):
    class Meta:
        model = LLM
        fields = ["name", "llm_class", 'config']