from django.shortcuts import render
from django.views.generic import TemplateView, CreateView, UpdateView, DeleteView, ListView, DetailView
from django.urls import reverse_lazy

from common.mixin import LoginRequiredMixin

from llm.models import LLM
from llm.form import LLMForm, Forms


class CreateLLMView(LoginRequiredMixin, CreateView):
    model = LLM
    template_name = 'llm/form.html'
    form_class = LLMForm
    success_url = reverse_lazy('llm:list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['llm_forms'] = Forms(self.user)
        context['is_new'] = True
        return context
    
    def form_valid(self, form):
        form.instance.user = self.usr
        return super().form_valid(form)

    def form_invalid(self, form):
        print("Form is invalid")
        print(form.errors)
        return super().form_invalid(form)


class LLMListView(LoginRequiredMixin, ListView):
    model = LLM
    template_name = 'llm/list.html'
    context_object_name = 'llms'

    def get_queryset(self):
        return LLM.objects.filter(user=self.usr)


class LLMDetailView(LoginRequiredMixin, DetailView):
    model = LLM
    template_name = 'llm/detail.html'
    context_object_name = 'llm'

    def get_queryset(self):
        return LLM.objects.filter(user=self.usr)


class LLMUpdateView(LoginRequiredMixin, UpdateView):
    model = LLM
    template_name = 'llm/form.html'
    form_class = LLMForm
    success_url = reverse_lazy('llm:list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        return kwargs

    def get_queryset(self):
        return LLM.objects.filter(user=self.usr)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['llm_forms'] = Forms(user=self.user, llm=self.get_object())
        context['is_new'] = False
        return context


class LLMDeleteView(LoginRequiredMixin, DeleteView):
    model = LLM
    template_name = 'llm/delete.html'
    success_url = reverse_lazy('llm:list')
    context_object_name = 'llm'

    def get_queryset(self):
        return LLM.objects.filter(user=self.usr)