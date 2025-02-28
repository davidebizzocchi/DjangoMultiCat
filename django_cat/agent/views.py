from django.shortcuts import redirect
from django.views.generic import ListView, DeleteView, DetailView, UpdateView, CreateView
from django.urls import reverse_lazy
from common.mixin import LoginRequiredMixin

from agent.models import Agent
from agent.forms import AgentForm

from icecream import ic


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

class AgentListView(AgentMixin, ListView):
    template_name = 'agent/list.html'
    context_object_name = 'agents'

    def get_queryset(self):
        ic(Agent.objects.filter_include_default(user=self.usr))
        return Agent.objects.filter_include_default(user=self.usr)

class AgentDetailView(AgentMixin, DetailView):
    object: "Agent"
    can_view_default = True
    template_name = 'agent/detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = AgentForm(instance=self.object, user=self.usr)
        return context

class AgentUpdateView(AgentMixin, UpdateView):
    template_name = 'agent/form.html'
    form_class = AgentForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.usr
        return kwargs

class AgentCreateView(AgentMixin, CreateView):
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


