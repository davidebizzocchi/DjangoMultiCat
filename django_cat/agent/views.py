from django.shortcuts import redirect
from django.views.generic import ListView, DeleteView, DetailView, UpdateView, CreateView
from django.urls import reverse_lazy

from common.mixin import LoginRequiredMixin
from common.form_pydantic import PydanticFormBuilder

from agent.models import Agent
from agent.forms import AgentForm
from llm.models import LLM

from icecream import ic

from django.conf import settings

class AgentMixin(LoginRequiredMixin):
    model = Agent
    can_view_default = False
    
    context_object_name = "agent"
    success_url = reverse_lazy('agent:list')
    
    slug_url_kwarg = "agent_id"
    slug_field = "agent_id"

    def get_object(self, queryset=None):
        object = super().get_object(queryset)

        if object.is_default and not self.usr.is_superuser and not self.usr.is_staff and not self.can_view_default:
            self.handle_no_permission()
        return object

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # The LLM queryset for the form is already handled in AgentForm's __init__
        # So, we don't need to explicitly pass llms for the form here.
        # However, if you need to display a list of LLMs separately from the form, you can add it here.
        # For example:
        # context["user_llms_list"] = LLM.objects.filter(user=self.usr)
        return context
    
class LLMSchemasMixin:
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # llm_schemas = self.user.client.get_llm_schemas()
        
        # # Create forms dictionary with humanReadableName as key
        # llm_forms = {}
        # llm_class_mapping = {}
        
        # for config_title, schema in llm_schemas.items():
        #     human_readable = schema.get("humanReadableName", config_title)
        #     form = PydanticFormBuilder.create_form_from_schema(schema, config_title)
            
        #     # Save original class name in form metadata
        #     form.original_class_name = config_title
            
        #     # Store form and update mapping
        #     llm_forms[human_readable] = form
        #     llm_class_mapping[human_readable] = config_title
        
        # # Recupera gli LLM dell'utente
        # user_llms = LLM.objects.filter(user=self.usr)
        # context["user_llms"] = user_llms
        
        # context["llm_forms"] = llm_forms
        # context["llm_class_mapping"] = llm_class_mapping

        context["llms"] = LLM.objects.filter(user=self.usr)
        return context


class AgentListView(AgentMixin, ListView):
    template_name = 'agent/list.html'
    context_object_name = 'agents'

    def get_queryset(self):
        return Agent.objects.filter_include_default(user=self.usr)

class AgentDetailView(AgentMixin, DetailView):
    object: "Agent"
    can_view_default = True
    template_name = 'agent/detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = AgentForm(instance=self.object, user=self.usr)
        # Pass the llm instance to the template if it exists
        if self.object.llm:
            context["llm_instance"] = self.object.llm
        return context

class AgentUpdateView(AgentMixin, LLMSchemasMixin, UpdateView):
    template_name = 'agent/form.html'
    form_class = AgentForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.usr
        return kwargs

class AgentCreateView(AgentMixin, LLMSchemasMixin, CreateView):
    template_name = 'agent/form.html'
    form_class = AgentForm

    def get_object(self, *args, **kwargs):
        return {
            "agent_id": "new",
        }
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.usr
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["is_new"] = True
        return context

class AgentDeleteView(AgentMixin, DeleteView):
    template_name = 'agent/delete_confirm.html'

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.object.is_default:
            return redirect('agent:list')
        return super().delete(request, *args, **kwargs)


