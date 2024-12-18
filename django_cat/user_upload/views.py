from django.shortcuts import render
from django.views.generic import CreateView, ListView, DeleteView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404
from django.contrib import messages
from user_upload.models import File, FileLibraryAssociation
from user_upload.forms import FileUploadForm
from icecream import ic


class FileUploadView(LoginRequiredMixin, CreateView):
    model = File
    form_class = FileUploadForm
    template_name = 'user_upload/file_upload.html'
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
                    f'File "{file.title}" caricato con successo.'
                )
                if uploaded:
                    messages.info(
                        self.request,
                        f'File aggiunto alle librerie: {", ".join(lib.name for lib in uploaded)}'
                    )
                
                def _on_step(perc):
                    ic(f'Lettura {file.title}: {perc}%')
                    messages.info(
                        self.request,
                        f'Lettura {file.title}: {perc}%'
                    )
                
                def _on_complete(thoughts):
                    ic(f'Completata lettura di {file.title} con {thoughts} thoughts')
                    messages.success(
                        self.request,
                        f'Completata lettura di {file.title} con {thoughts} thoughts'
                    )

                handler_id = file.wait_ingest(_on_step, _on_complete)
                
            else:
                messages.warning(
                    self.request,
                    f'Il file "{file.title}" esiste già nel sistema.'
                )
        
        return super().form_valid(form)


class FileListView(LoginRequiredMixin, ListView):
    model = File
    template_name = 'user_upload/file_list.html'
    context_object_name = 'files'

    def get_queryset(self):
        return File.objects.filter(user=self.request.user)

class FileDeleteView(LoginRequiredMixin, DeleteView):
    model = File
    template_name = 'user_upload/file_delete.html'
    success_url = reverse_lazy('file:list')
    context_object_name = 'file'
    slug_field = 'file_id'
    slug_url_kwarg = 'file_id'

    def get_queryset(self):
        return File.objects.filter(user=self.request.user)

    def post(self, request, *args, **kwargs):
        file = self.get_object()
        messages.error(request, f'File "{file.title}" eliminato con successo.')
        return super().post(request, *args, **kwargs)

class FileAssociationView(LoginRequiredMixin, UpdateView):
    model = File
    form_class = FileUploadForm
    template_name = 'user_upload/file_assoc.html'
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
                f'File "{file}" aggiunto alle librerie: {", ".join(lib.name for lib in uploaded)}'
            )
        if deleted:
            ic(deleted)
            messages.error(
                self.request,
                f'File "{file}" rimosso dalle librerie: {", ".join(lib.name for lib in deleted)}'
            )
        
        return super().form_valid(form)
