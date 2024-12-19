import hashlib
from pathlib import Path
import threading
import time
from typing import Union
import uuid
from django.conf import settings
from django.db import models
from app.utils import BaseUserModel
from cheshire_cat.types import Notification
from user_upload.fields import FileObject, FileObjectDecoder, FileObjectEncoder
from decouple import config
from library.models import Library
import re
from threading import Event
from icecream import ic


class FileLibraryAssociation(models.Model):
    file = models.ForeignKey('File', on_delete=models.CASCADE, related_name='associations')
    library = models.ForeignKey(Library, on_delete=models.CASCADE, related_name='associations')


    def save(self, *args, **kwargs):
        self.library.add_file_to_existing_chats(str(self.file.file_id))

        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        self.library.remove_file_from_existing_chats(str(self.file.file_id))

        super().delete(*args, **kwargs)
    

    def __str__(self):
        return f"{self.file} in {self.library}"
    
    class Meta:
        verbose_name = 'file library association'
        verbose_name_plural = 'file library associations'

class File(BaseUserModel):
    title = models.CharField(max_length=255, default="")
    file: FileObject = models.JSONField(encoder=FileObjectEncoder, decoder=FileObjectDecoder)
    file_id = models.CharField(max_length=255, unique=True, default=uuid.uuid4)
    hash = models.CharField(null=True, blank=True)
    ingested = models.BooleanField(default=False)

    @property 
    def libraries(self):
        """Returns all libraries associated with this file with optimized query"""
        return Library.objects.filter(
            associations__file=self
        ).select_related('user').only(
            'id', 
            'name',
            'library_id',
            'user__username'
        )

    def _get_library_from_id(self, library_id: str):
        return Library.objects.get(library_id=library_id)

    def check_assoc(self, library: Union[str, Library]) -> bool:
        if isinstance(library, str):
            library = self._get_library_from_id(library)

        return FileLibraryAssociation.objects.filter(file=self, library=library).exists()

    def assoc_library(self, library: Union[str, Library]):
        if isinstance(library, str):
            library = self._get_library_from_id(library)

        if not self.check_assoc(library):
            return FileLibraryAssociation.objects.create(file=self, library=library)
        
    def delete_library(self, library: Union[str, Library]):
        if isinstance(library, str):
            library = self._get_library_from_id(library)

        if self.check_assoc(library):
            return FileLibraryAssociation.objects.filter(file=self, library=library).delete()
        
    def assoc_library_list(self, libraries: list):
        for library in libraries:
            if isinstance(library, str):
                library = self._get_library_from_id(library)

            self.assoc_library(library)

    def delete_in_library_list(self, libraries: list):
        for library in libraries:
            if isinstance(library, str):
                library = self._get_library_from_id(library)

            self.delete_library(library)

    def is_ingested(self):
        if self.ingested:
            return True
        
    def wait_ingest(self, callback_on_step=None, callback_on_complete=None):
        file_id = str(self.file_id)
        handler_refs = {'id': None}  # Dizionario per mantenere il riferimento

        def handle_notification(notification: Notification):
            message = notification.message

            ic(f"Notification received: {message}")
            ic(callback_on_step, callback_on_complete)
            
            # Match per il progresso di lettura
            if match := re.match(r"Read (\d+)% of (.+)", message):
                percentage, source = match.groups()
                ic(percentage, source)
                if file_id in source:  # Verifichiamo che la notifica sia per questo file
                    if callback_on_step is not None:
                        callback_on_step(int(percentage))
                
            # Match per il completamento
            elif match := re.match(r"Finished reading (.+), I made (\d+) thoughts on it\.", message):
                source, thoughts = match.groups()
                ic(source, thoughts)
                if file_id in source:  # Verifichiamo che la notifica sia per questo file
                    self.ingested = True
                    self.save()
                    if callback_on_complete is not None:
                        callback_on_complete(int(thoughts))
                    
                    # Usa il riferimento dal dizionario
                    ic(handler_refs['id'])
                    self.client.unregister_notification_handler(handler_refs['id'])

        # Salva l'ID nel dizionario di riferimento
        handler_refs['id'] = self.client.register_notification_handler(handle_notification, callback_on_step, callback_on_complete)
        return handler_refs['id']

    def upload(self):
        """
        Store file in the cat with metadata including author and file_id
        """
        metadata = {
            "file_id": str(self.file_id)
        }

        ic(self.client.upload_file(self, metadata))
        
        # with open(self.file.path, 'rb') as f:
        #     self.client.rabbit_hole.upload_file(
        #         file=f.read(),  # Pass bytes directly
        #         metadata=metadata
        #     )

    def wait_upload(self):
        """
        Wait for file to be ready before uploading.
        Timeout after WAIT_UPLOAD seconds (default 30s)
        """
        timeout_seconds = config("WAIT_UPLOAD", cast=int, default=30)  # timeout in seconds
        start = time.time()
        
        while not self.file.path.exists():
            time.sleep(0.2)  # check every 200ms
            
            if time.time() - start > timeout_seconds:
                return
            
        self.upload()
    
    @property
    def link(self):
        return (
            f"/media/{self.file.path.relative_to(settings.MEDIA_ROOT)}"
        )  # Attenzione se viene cambiato il nome nella cartella in docker

    @classmethod
    def calculate_file_hash(self, file: Path) -> str:
        hasher = hashlib.md5()
        with open(file, "rb") as f:
            while chunk := f.read(8192):
                hasher.update(chunk)
        return hasher.hexdigest()
    
    @classmethod
    def calculate_file_has_from_instance(self, file):
        hasher = hashlib.md5()

        for chunk in file.chunks():
            hasher.update(chunk)

        return hasher.hexdigest()
    
    def save(self, *args, **kwargs):
        """
        Esegue azioni al salvataggio del modello

        Se l'hash non è definito, lo genera.
        Imposta come titolo il nome del file (inclusa estensione)
        """
        if not self.pk:
            threading.Thread(target=self.wait_upload).start()

        if not self.pk:
            self.calculate_file_hash(self.file.path)


        if not self.title:
            self.title = self.file.path.name

        super().save(*args, **kwargs)

    def delete(self):
        """
        Esegue azioni alla cancellazione del modello

        Cancella il file dal filesystem
        """

        ic(self.client.delete_file(self))

        self.file.path.unlink()
        super().delete()

    def __str__(self):
        return self.title
    
    class Meta:
        verbose_name = 'file'
        verbose_name_plural = 'files'
