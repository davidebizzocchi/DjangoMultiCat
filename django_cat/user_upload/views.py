from django.shortcuts import render
from django.views.generic import CreateView, ListView, DeleteView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404
from .models import File, FileLibraryAssociation
from .forms import FileUploadForm, FileAssociationForm

class FileUploadView(LoginRequiredMixin, CreateView):
    model = File
    form_class = FileUploadForm
    template_name = 'user_upload/file_upload.html'
    success_url = reverse_lazy('chat:file_list')

    def form_valid(self, form):
        form.instance.userprofile = self.request.user.userprofile
        return super().form_valid(form)

class FileListView(LoginRequiredMixin, ListView):
    model = File
    template_name = 'user_upload/file_list.html'
    context_object_name = 'files'

    def get_queryset(self):
        return File.objects.filter(userprofile=self.request.user.userprofile)

class FileDeleteView(LoginRequiredMixin, DeleteView):
    model = File
    template_name = 'user_upload/file_delete.html'
    success_url = reverse_lazy('chat:file_list')
    context_object_name = 'file'
    slug_field = 'file_id'
    slug_url_kwarg = 'file_id'

    def get_queryset(self):
        return File.objects.filter(userprofile=self.request.user.userprofile)

class FileAssociationView(LoginRequiredMixin, UpdateView):
    model = File
    form_class = FileAssociationForm
    template_name = 'user_upload/file_assoc.html'
    success_url = reverse_lazy('chat:file_list')
    slug_field = 'file_id'
    slug_url_kwarg = 'file_id'

    def get_queryset(self):
        return File.objects.filter(userprofile=self.request.user.userprofile)

    def form_valid(self, form):
        response = super().form_valid(form)
        selected_libraries = form.cleaned_data['libraries']
        self.object.assoc_library_list(selected_libraries)
        return response
