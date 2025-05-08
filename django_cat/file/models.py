import hashlib
import threading
from pathlib import Path
import io
import time
from typing import Union
import uuid
from decouple import config
from icecream import ic
from django.conf import settings
from django.db import models

from common.utils import BaseUserModel
from library.models import Library
from cheshire_cat.types import DocReadingProgress
from file.fields import (
    FileObject,
    FileObjectDecoder,
    FileObjectEncoder,
    IngestionConfig,
    IngestionConfigEncoder,
    IngestionConfigDecoder,
    IngestionType
)
from file.utils import (
    process_image_ocr,
    get_image_from_file,
    save_processed_text,
    extract_and_validate_json,
    update_processed_text,
    next_file_path
)


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
    PENDING_PROCESS = 'pending_process'  # New status
    PENDING_UPLOAD = 'pending_upload'
    READY = 'ready'
    STATUS_CHOICES = [
        (PENDING_CONFIG, 'Configuring'),
        (PENDING_PROCESS, 'Post processing'), 
        (PENDING_UPLOAD, 'Uploading'),
        (READY, 'Ready'),
    ]
    
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES,
        default=PENDING_CONFIG
    )
    config_progress = models.IntegerField(default=0)  # OCR completion percentage
    
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
        """Check if a library is associated with this file"""
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
            for assoc in FileLibraryAssociation.objects.filter(file=self, library=library):
                assoc.delete()
        
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
        # Dictionary to keep the reference
        # is used as closure for keep the associated handler ID
        # Critical: The handler must unregister itself since the client can't determine when to do so.
        handler_refs = {'id': None}
        file_id = str(self.file_id)  # Because file_id is a UUID

        def handle_notification(notification: DocReadingProgress):
            """
            Handle notifications from the Cheshire Cat about the file ingestion progress.
            Check if the notification is for the current file (trhough source_id == file_id)
            The notification status can be "progress" or "done".
            Call callbacks if needed and set attributes accordingly.
            At end unregister the handler (itself).
            """
            if notification.type == "doc-reading-progress":
                # Extracts the part before the first dot
                # This is the file_id
                source_id = notification.source.split('.', 1)[0] if '.' in notification.source else notification.source
                if file_id == source_id:
                    if notification.status == "progress":
                        self.config_progress = notification.perc_read
                        self.save(update_fields=['config_progress'])
                        
                        if callback_on_step is not None:
                            callback_on_step(int(notification.perc_read))

                    elif notification.status == "done":
                        self.ingested = True
                        self.status = self.READY

                        self.save(update_fields=['status', "ingested"])

                        if callback_on_complete is not None:
                            callback_on_complete()

                        self.client.unregister_notification_handler(handler_refs['id'])

        # Register the notification handler
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

        # File is ready, proceed with configuration
        self.status = self.PENDING_CONFIG
        self.config_progress = 0
        self.save(update_fields=['status', 'config_progress'])
        self.apply_config_file()

        # Add post-processing
        self.status = self.PENDING_PROCESS
        self.config_progress = 0
        self.save(update_fields=['status', 'config_progress'])
        self.post_process()

        # Upload the file in the Cat
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
        )

    @classmethod
    def calculate_file_hash(self, file: Path) -> str:
        """Calculate file hash for deduplication"""
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
        Save the processed file and update path
        """
        self.file = FileObject(path=new_path)  # Let FileObject determine the new size
        self.save(update_fields=['file'])
    
    def apply_config_file(self, use_page_separator=False):
        """
        Process file based on ingestion configuration and save result.
        If it's an audio file, it will be transcribed and the original deleted.
        If it's an image/PDF, OCR will be applied if configured.
        """
        if self.ingestion_config.is_audio:
            try:
                original_audio_path = self.file.path
                
                if not self.hash:
                    # Fallback - hash should be set by self.save() before calling wait_upload -> apply_config_file
                    self.hash = self.calculate_file_hash(original_audio_path)
                    # Don't save here to avoid recursion or thread issues, hash should be persisted before
                    # Consider logging a warning if hash is not present at this point
                    ic(f"Warning: File hash was not set before apply_config_file for {original_audio_path}. Calculating now.")
                    if not self.hash:  # If still not available after calculation
                        raise ValueError("File hash is not available for naming transcribed file and could not be calculated.")

                raw_audio_bytes = original_audio_path.read_bytes()
                audio_object = io.BytesIO(raw_audio_bytes)

                # Assuming self.client.transcribe exists and returns transcribed text
                transcribed_text = self.client.transcribe(audio_object)

                new_text_filename = f"{self.hash}.txt"
                new_text_path = original_audio_path.parent / new_text_filename
                
                new_text_path.write_text(transcribed_text, encoding='utf-8')
                
                # Update file object to point to the new text file
                # Size will be recalculated by FileObject
                self.file = FileObject(path=new_text_path) 
                # Save only file field to update path and recalculated size
                # This save() should not trigger wait_upload again because pk exists
                super().save(update_fields=['file']) 

                # Delete the original audio file
                original_audio_path.unlink()
                
                self.config_progress = 100
                super().save(update_fields=['config_progress'])  # Use super().save to avoid full save() logic

            except Exception as e:
                ic(f"Error processing audio file: {str(e)}")
                raise ValueError(f"Error processing audio file: {str(e)}")
            return

        elif self.ingestion_config.is_ocr:
            try:
                images = get_image_from_file(self.file.path)
                texts = []
                page_counter = 1
                
                # Handle both list of images (PDF) and single image
                image_list = images if isinstance(images, list) else [images]
                total_images = len(image_list)
                
                for idx, img in enumerate(image_list, 1):
                    # Process OCR for the current image
                    page_texts = process_image_ocr(img, is_double_page=self.ingestion_config.is_double_page)
                    
                    # Add page number to each extracted text
                    for text in page_texts:
                        texts.append(f"{text}\n[Page {page_counter}]\n")
                        page_counter += 1
                    
                    # Update progress
                    self.config_progress = int((idx / total_images) * 100)
                    self.save(update_fields=['config_progress'])
                
                # Join texts with or without separator
                separator = "\n\n=== NEW PAGE ===\n\n" if use_page_separator else "\n"
                processed_text = separator.join(texts)

                self.processed_text = processed_text
                
                # Save the result
                new_path = save_processed_text(processed_text, self.file.path.absolute())
                self.save_processed_file(new_path)
                    
            except Exception as e:
                raise ValueError(f"Error processing file: {str(e)}")

    def call_llm(self, prompt: str):
        token = self.client.count_token(prompt)

        # Calculate the minimum time required between requests
        max_tokens_per_minute = 6000
        minutes_per_token = 1 / max_tokens_per_minute
        wait_time = token * minutes_per_token * 60  # Convert to seconds
        time.sleep(wait_time + 2)

        chat_id = self.client.chat_completition(prompt)
        return self.client.wait_message_content(chat_id).text

    def post_process(self):
        """
        Execute post-configuration processing before upload based on selected type.
        """
        if not self.ingestion_config.needs_post_process:
            return

        # NOTE: The output of .call_llm() must be a JSON object with a "new_text" field
        try:
            prompt = self.ingestion_config.get_prompt()

            if not prompt:
                return
            
            # Get thee content to process
            content = getattr(self, "processed_text", None)
            if content is None:
                with open(self.file.path.absolute(), 'r') as f:
                    content = f.read()

            new_file_path = next_file_path(self.file.path).with_suffix('.txt')

            # If is OCR
            if self.ingestion_config.is_ocr:
                # Divide the content into pages using the delimiter
                pages = content.split("\n")
                total_pages = len(pages)
                previous_text = ""
                for idx, line in enumerate(pages):
                    if line.strip().startswith('[Page ') and line.strip().endswith(']'):
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
            # If not OCR
            else:
                # Separate the context using "." as delimiter
                pieces = content.split(".")
                total_pieces = len(pieces)
                for idx, piece in enumerate(pieces):
                    request = prompt + piece
                    result = self.call_llm(request)
                    json_data = extract_and_validate_json(result)

                    processed_text = json_data["new_text"]
                    update_processed_text(processed_text, new_file_path)

                    self.config_progress = int(((idx + 1) / total_pieces) * 100)
                    self.save(update_fields=['config_progress'])

            self.save_processed_file(new_file_path)

        except Exception as e:
            raise ValueError(f"Error in post-processing: {str(e)}")
        finally:
            pass

    def save(self, *args, **kwargs):
        """
        Execute actions on model save
        If hash not defined, generate it.
        Set file name (including extension) as title
        """
        is_new = not self.pk

        if is_new and self.file and self.file.path.exists():
            if not self.hash:
                self.hash = self.calculate_file_hash(self.file.path)
            if not self.title:
                self.title = self.file.path.name

        super().save(*args, **kwargs)

        if is_new:
            self.wait_ingest()
            threading.Thread(target=self.wait_upload).start()

    def delete(self):
        """
        Execute actions on model delete.
        Delete main file and all associated processed files.
        """
        # Delete the file from the cat
        ic(self.client.delete_file(self))
        
        # Find and delete all associated files
        base_path = self.file.path.parent
        base_name = self.hash
        
        # Search for files with pattern name_1.txt, name_2.txt, etc.
        for file_path in base_path.glob(f"{base_name}*.*"):
            try:
                file_path.unlink()
            except FileNotFoundError:
                continue
                
        # Delete the original file
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
