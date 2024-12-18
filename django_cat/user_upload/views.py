from django.shortcuts import render
from django.views.generic import CreateView, ListView, DeleteView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404
from django.contrib import messages
from user_upload.models import File, FileLibraryAssociation
from user_upload.forms import FileUploadForm

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
                
                # Registra handler per le notifiche di ingestione
                handler_id = file.wait_ingest()
                
                def handle_ingest_notification(notification):
                    result = notification
                    if result and isinstance(result, dict):
                        if result["type"] == "progress":
                            messages.info(
                                self.request,
                                f'Lettura {result["filename"]}: {result["percentage"]}%'
                            )
                        elif result["type"] == "complete":
                            messages.success(
                                self.request,
                                f'Completata lettura di {result["filename"]} con {result["thoughts"]} thoughts'
                            )
                            # Rimuovi l'handler una volta completato
                            file.client.unregister_notification_handler(handler_id)
                
                file.client.register_notification_handler(handle_ingest_notification)
                
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

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        kwargs['instance'] = self.get_object()
        return kwargs

    def form_valid(self, form):
        response = super().form_valid(form)
        saved_files = form.save()
        
        for _, file, uploaded, deleted in saved_files:
            if uploaded:
                messages.error(
                    self.request,
                    f'File aggiunto alle librerie: {", ".join(lib.name for lib in uploaded)}'
                )
            if deleted:
                messages.success(
                    self.request,
                    f'File rimosso dalle librerie: {", ".join(lib.name for lib in deleted)}'
                )
        
        return response
