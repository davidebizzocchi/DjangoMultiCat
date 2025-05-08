from django.shortcuts import render
from django.views.generic import CreateView, ListView, DeleteView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404
from django.contrib import messages
from file.models import File, FileLibraryAssociation
from file.forms import FileUploadForm
from icecream import ic


class FileUploadView(LoginRequiredMixin, CreateView):
    model = File
    form_class = FileUploadForm
    template_name = 'file/upload.html'
    success_url = reverse_lazy('file:list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_success_url(self):
        return self.success_url

    def form_valid(self, form):
        saved_files = form.save()
    
        for created, file, uploaded, deleted in saved_files:
            if created:
                messages.success(
                    self.request,
                    f'File "{file.title}" uploaded successfully.'
                )
                if uploaded:
                    messages.info(
                        self.request,
                        f'File added to libraries: {", ".join(lib.name for lib in uploaded)}'
                    )
            else:
                messages.warning(
                    self.request,
                    f'File "{file.title}" already exists in the system.'
                )
    
        return super().form_valid(form)


class FileListView(LoginRequiredMixin, ListView):
    model = File
    template_name = 'file/list.html'
    context_object_name = 'files'

    def get_queryset(self):
        return File.objects.filter(user=self.request.user)

class FileDeleteView(LoginRequiredMixin, DeleteView):
    model = File
    template_name = 'file/delete.html'
    success_url = reverse_lazy('file:list')
    context_object_name = 'file'
    slug_field = 'file_id'
    slug_url_kwarg = 'file_id'

    def get_queryset(self):
        return File.objects.filter(user=self.request.user)

    def post(self, request, *args, **kwargs):
        file = self.get_object()
        messages.error(request, f'File "{file.title}" deleted successfully.')
        return super().post(request, *args, **kwargs)

class FileAssociationView(LoginRequiredMixin, UpdateView):
    model = File
    form_class = FileUploadForm
    template_name = 'file/assoc.html'
    success_url = reverse_lazy('file:list')
    slug_field = 'file_id'
    slug_url_kwarg = 'file_id'

    def get_success_url(self):
        return self.success_url

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        kwargs['instance'] = self.get_object()
        return kwargs

    def form_valid(self, form):
        _, file, uploaded, deleted = form.save()

        if uploaded:
            ic(uploaded)
            messages.success(
                self.request,
                f'File "{file}" added to libraries: {", ".join(lib.name for lib in uploaded)}'
            )
        if deleted:
            ic(deleted)
            messages.error(
                self.request,
                f'File "{file}" removed from libraries: {", ".join(lib.name for lib in deleted)}'
            )
    
        return super().form_valid(form)
