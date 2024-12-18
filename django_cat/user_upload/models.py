import hashlib
from pathlib import Path
import threading
import time
from typing import Union
import uuid
from django.conf import settings
from django.db import models
from app.utils import BaseUserModel
from django_cat.cheshire_cat.types import Notification
from user_upload.fields import FileObject, FileObjectDecoder, FileObjectEncoder
from decouple import config
from library.models import Library
import re
from threading import Event


class FileLibraryAssociation(models.Model):
    file = models.ForeignKey('File', on_delete=models.CASCADE, related_name='libraries')
    library = models.ForeignKey(Library, on_delete=models.CASCADE, related_name='files')

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
    library = models.ForeignKey(Library, on_delete=models.CASCADE, related_name='files')
    ingested = models.BooleanField(default=False)

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
        
    def assoc_library_list(self, libraries: list):
        for library in libraries:
            if isinstance(library, str):
                library = self._get_library_from_id(library)

            self.assoc_library(library)

    def is_ingested(self):
        if self.ingested:
            return True
        
    def wait_ingest(self, request):
        ingest_complete = Event()
        progress = {"current": 0}
        file_id = str(self.file_id)
        
        def handle_notification(notification: Notification):
            message = notification.message
            
            # Match per il progresso di lettura
            if match := re.match(r"Read (\d+)% of (.+)", message):
                percentage, source = match.groups()
                if file_id in source:  # Verifichiamo che la notifica sia per questo file
                    progress["current"] = int(percentage)
                
            # Match per il completamento
            elif match := re.match(r"Finished reading (.+), I made (\d+) thoughts on it\.", message):
                source, thoughts = match.groups()
                if file_id in source:  # Verifichiamo che la notifica sia per questo file
                    progress["thoughts"] = int(thoughts)
                    progress["source"] = source
                    ingest_complete.set()

        # Registra l'handler per le notifiche e salva l'ID
        handler_id = self.client.register_notification_handler(handle_notification)
        
        try:
            # Aspetta il completamento o il timeout
            timeout = config("INGEST_TIMEOUT", cast=int, default=300)  # 5 minuti default
            if ingest_complete.wait(timeout):
                self.ingested = True
                self.save()
                return progress
            return {"error": "Timeout during ingestion"}
        finally:
            # Rimuovi l'handler usando il suo ID
            self.client.unregister_notification_handler(handler_id)

    def upload(self):
        """
        Store file in the cat with metadata including author and file_id
        """
        file_id = str(self.file_id)
        metadata = {
            "author": self.userprofile.cheschire_id,
            "source": file_id
        }
        
        with open(self.file.path, 'rb') as f:
            self.client.rabbit_hole.upload_file(
                file=f,
                metadata=metadata
            )

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

    def __str__(self):
        return self.title
    
    class Meta:
        verbose_name = 'file'
        verbose_name_plural = 'files'
