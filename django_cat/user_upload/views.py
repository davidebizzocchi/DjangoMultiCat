from django.shortcuts import render
from django.views.generic import CreateView, ListView, DeleteView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404
from user_upload.models import File, FileLibraryAssociation
from user_upload.forms import FileUploadForm

class FileUploadView(LoginRequiredMixin, CreateView):
    model = File
    form_class = FileUploadForm
    template_name = 'user_upload/file_upload.html'
    success_url = reverse_lazy('chat:file_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        saved_files = form.save()
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
    form_class = FileUploadForm
    template_name = 'user_upload/file_assoc.html'
    success_url = reverse_lazy('chat:file_list')
    slug_field = 'file_id'
    slug_url_kwarg = 'file_id'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        kwargs['instance'] = self.get_object()
        return kwargs
