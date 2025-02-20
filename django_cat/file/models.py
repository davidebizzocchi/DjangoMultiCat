import hashlib
from pathlib import Path
import threading
import time
from typing import Union
import uuid
from django.conf import settings
from django.db import models
from common.utils import BaseUserModel
from cheshire_cat.types import DocReadingProgress
from file.fields import FileObject, FileObjectDecoder, FileObjectEncoder, IngestionConfig, IngestionConfigEncoder, IngestionConfigDecoder, IngestionType, PageMode, PostProcessType
from decouple import config
from library.models import Library
import re
from threading import Event
from icecream import ic
from PIL import Image
from file.utils import process_image_ocr, get_image_from_file, save_processed_text, extract_and_validate_json, update_processed_text, next_file_path


class FileLibraryAssociation(models.Model):
    file = models.ForeignKey('File', on_delete=models.CASCADE, related_name='associations')
    library = models.ForeignKey(Library, on_delete=models.CASCADE, related_name='associations')


    def save(self, *args, **kwargs):
        threading.Thread(self.file.wait_until_ingested(self.library.add_file_to_existing_chats, str(self.file.file_id))).start()
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
    # Rimuovi la vecchia classe IngestionFlags
    title = models.CharField(max_length=255, default="")
    file: FileObject = models.JSONField(encoder=FileObjectEncoder, decoder=FileObjectDecoder)
    file_id = models.CharField(max_length=255, unique=True, default=uuid.uuid4)
    hash = models.CharField(null=True, blank=True)
    ingested = models.BooleanField(default=False)
    ingestion_config: IngestionConfig = models.JSONField(
        encoder=IngestionConfigEncoder,
        decoder=IngestionConfigDecoder,
        default=IngestionConfig,
    )
    PENDING_CONFIG = 'pending_config'
    PENDING_PROCESS = 'pending_process'  # Nuovo stato
    PENDING_UPLOAD = 'pending_upload'
    READY = 'ready'
    STATUS_CHOICES = [
        (PENDING_CONFIG, 'In configurazione'),
        (PENDING_PROCESS, 'Post processing'),  # Nuovo stato
        (PENDING_UPLOAD, 'In caricamento'),
        (READY, 'Pronto'),
    ]
    
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES,
        default=PENDING_CONFIG
    )
    config_progress = models.IntegerField(default=0)  # Percentuale di completamento OCR
    
    @property
    def is_configuring(self):
        return self.status == self.PENDING_CONFIG
        
    @property
    def is_uploading(self):
        return self.status == self.PENDING_UPLOAD
        
    @property 
    def is_ready(self):
        return self.status == self.READY

    @property
    def is_processing(self):
        return self.status == self.PENDING_PROCESS

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

        def handle_notification(notification: DocReadingProgress):
            
            if notification.type == "doc-reading-progress":
                # Estrae la parte prima del primo punto
                source_id = notification.source.split('.', 1)[0] if '.' in notification.source else notification.source
                if file_id == source_id:
                    ic(notification.status)
                    if notification.status == "progress":
                        self.config_progress = notification.perc_read
                        self.save(update_fields=['config_progress'])
                        
                        ic(self.config_progress, notification.perc_read)

                        if callback_on_step is not None:
                            callback_on_step(int(notification.perc_read))

                    elif notification.status == "done":
                        self.ingested = True
                        self.status = self.READY


                        self.save(update_fields=['status', "ingested"])

                        if callback_on_complete is not None:
                            callback_on_complete()

                        self.client.unregister_notification_handler(handler_refs['id'])

        # Salva l'ID nel dizionario di riferimento
        handler_refs['id'] = self.client.register_notification_handler(handle_notification)
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
        
        while not self.file.path.exists() or not self.pk:
            time.sleep(0.2)  # check every 200ms
            
            if time.time() - start > timeout_seconds:
                return
            
        self.status = self.PENDING_CONFIG
        self.config_progress = 0
        self.save(update_fields=['status', 'config_progress'])
        self.apply_config_file()

        # Aggiungi il post-processing
        self.status = self.PENDING_PROCESS
        self.config_progress = 0
        self.save(update_fields=['status', 'config_progress'])
        self.post_process()
        
        self.status = self.PENDING_UPLOAD
        self.config_progress = 0
        self.save(update_fields=['status', 'config_progress'])
        self.upload()

    def wait_until_ingested(self, callback=None, *callback_args, wait_time=0.5):
        """
        Wait until the file is ingested
        Args:
            callback: function to call after ingestion is complete
            *callback_args: arguments to pass to the callback function
            wait_time: time to wait between checks (default: 0.5 seconds)
        """
        while not self.ingested:
            time.sleep(wait_time)
            self.refresh_from_db()
        
        if callback is not None:
            callback(*callback_args)
    
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
    
    def save_processed_file(self, new_path: Path | str):
        """
        Salva il file processato e aggiorna il percorso
        """
        self.file = FileObject(path=new_path, size=self.file.size)
        self.save(update_fields=['file'])
    
    def apply_config_file(self, use_page_separator=False):
        """
        Processa il file in base alla configurazione di ingestione e salva il risultato
        """
        if not self.ingestion_config.is_ocr:
            return
        
        try:
            images = get_image_from_file(self.file.path)
            texts = []
            page_counter = 1
            
            # Gestione sia per lista di immagini (PDF) che singola immagine
            image_list = images if isinstance(images, list) else [images]
            total_images = len(image_list)
            
            for idx, img in enumerate(image_list, 1):
                # Process OCR per l'immagine corrente
                page_texts = process_image_ocr(img, is_double_page=self.ingestion_config.is_double_page)
                
                # Aggiungi numero pagina ad ogni testo estratto
                for text in page_texts:
                    texts.append(f"{text}\n[Pagina {page_counter}]\n")
                    page_counter += 1
                
                # Aggiorna progresso
                self.config_progress = int((idx / total_images) * 100)
                self.save(update_fields=['config_progress'])
            
            # Unisci i testi con o senza separatore
            separator = "\n\n=== NUOVA PAGINA ===\n\n" if use_page_separator else "\n"
            processed_text = separator.join(texts)

            self.processed_text = processed_text
            
            # Salva il risultato
            new_path = save_processed_text(processed_text, self.file.path.absolute())
            self.save_processed_file(new_path)
                
        except Exception as e:
            raise ValueError(f"Errore nel processing del file: {str(e)}")

    def call_llm(self, prompt: str):
        token = self.client.count_token(prompt)

        # Calcola il tempo minimo necessario tra le richieste
        max_tokens_per_minute = 6000

        minutes_per_token = 1 / max_tokens_per_minute
        wait_time = token * minutes_per_token * 60  # Converti in secondi

        ic(token, minutes_per_token, wait_time)
        # time.sleep(wait_time + 2)

        chat_id = self.client.chat_completition(prompt)

        return self.client.wait_message_content(chat_id).content

    def post_process(self):
        """
        Esegue elaborazioni post-configurazione prima dell'upload in base al tipo selezionato
        """
        if not self.ingestion_config.needs_post_process:
            return

        try:
            if self.ingestion_config.type == IngestionType.OCR:
                prompt = self.ingestion_config.get_prompt()

                if not prompt:
                    return
                
                content = getattr(self, "processed_text", None)
                if content is None:
                    ic(self.file.path.absolute())
                    with open(self.file.path.absolute(), 'r') as f:
                        content = f.read()


                new_file_path = next_file_path(self.file.path).with_suffix('.txt')

                # Divide il contenuto in pagine usando il delimitatore
                pages = content.split("\n")
                total_pages = len(pages)
                previous_text = ""

                for idx, line in enumerate(pages):
                    if line.strip().startswith('[Pagina ') and line.strip().endswith(']'):
                    #     if current_page:
                    #         pages.append('\n'.join(current_page))
                    #     current_page = []
                    # else:
                    #     current_page.append(line)

                        if previous_text == "":
                            continue

                        request = prompt + previous_text
                        result = self.call_llm(request)

                        json_data = extract_and_validate_json(result)

                        processed_text = json_data["new_text"]
                        processed_text += "\n" + line + "\n"

                        update_processed_text(result, new_file_path)
                        previous_text = ""

                        self.config_progress = int(((idx +1) / total_pages) * 100)
                        self.save(update_fields=['config_progress'])

                    previous_text += line + "\n"

                self.save_processed_file(new_file_path)
                

        except Exception as e:
            raise ValueError(f"Errore nel post-processing del file: {str(e)}")
        finally:
            pass

    def save(self, *args, **kwargs):
        """
        Esegue azioni al salvataggio del modello

        Se l'hash non è definito, lo genera.
        Imposta come titolo il nome del file (inclusa estensione)
        """
        if not self.pk:
            self.wait_ingest()
            threading.Thread(target=self.wait_upload).start()

        if not self.pk:
            self.calculate_file_hash(self.file.path)


        if not self.title:
            self.title = self.file.path.name

        super().save(*args, **kwargs)

    def delete(self):
        """
        Esegue azioni alla cancellazione del modello.
        Cancella il file principale e tutti i file processati associati.
        """
        # Elimina il file dal cat
        ic(self.client.delete_file(self))
        
        # Trova e elimina tutti i file associati
        base_path = self.file.path.parent
        base_name = self.hash
        
        # Cerca file con pattern nome_1.txt, nome_2.txt, ecc
        for file_path in base_path.glob(f"{base_name}*.*"):
            try:
                file_path.unlink()
            except FileNotFoundError:
                continue
                
        # Elimina il file originale
        try:
            self.file.path.unlink()
        except FileNotFoundError:
            pass

        super().delete()

    def __str__(self):
        return self.title
    
    class Meta:
        verbose_name = 'file'
        verbose_name_plural = 'files'
