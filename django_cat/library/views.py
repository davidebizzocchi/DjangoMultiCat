from django.shortcuts import redirect
from django.views.generic import CreateView, DeleteView, DetailView, ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from library.models import Library
from library.forms import LibraryForm


class NewLibraryView(LoginRequiredMixin, CreateView):
    model = Library
    template_name = 'library/new.html'
    form_class = LibraryForm

    def form_valid(self, form):
        form.instance.user = self.request.user
        library = form.save()
        return redirect('library:list')

class DeleteLibraryView(LoginRequiredMixin, DeleteView):
    model = Library
    template_name = 'library/delete_confirm.html'
    success_url = reverse_lazy('library:list')
    slug_field = 'library_id'
    slug_url_kwarg = 'library_id'

    def get_queryset(self):
        return self.model.objects.filter(user=self.request.user)

class LibraryDetailView(LoginRequiredMixin, DetailView):
    model = Library
    template_name = 'library/detail.html'
    context_object_name = 'library'
    slug_field = 'library_id'
    slug_url_kwarg = 'library_id'

    def get_queryset(self):
        return self.model.objects.filter(user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # I file sono già ottimizzati dal property method
        context['files'] = self.object.files
        # Otteniamo le chat con solo i campi necessari
        context['chats'] = self.object.chats.only(
            'chat_id'
        )
        return context

class LibraryListView(LoginRequiredMixin, ListView):
    model = Library
    template_name = 'library/list.html'
    context_object_name = 'libraries'

    def get_queryset(self):
        return self.model.objects.filter(user=self.request.user)
