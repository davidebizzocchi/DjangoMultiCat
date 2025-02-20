import os
from pathlib import Path
from typing import List
from django.conf import settings
from django.core.files.uploadedfile import InMemoryUploadedFile
from django import forms
from icecream import ic

from library.models import Library
from file.fields import FileObject, IngestionConfig, IngestionType, PageMode, PostProcessType
from file.models import File


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            result = [single_file_clean(d, initial) for d in data]
        else:
            result = [single_file_clean(data, initial)]
        
        return result


class FileUploadForm(forms.Form):
    file = MultipleFileField()
    ingestion_type = forms.ChoiceField(
        choices=[
            (IngestionType.NORMAL.value, 'Normale'),
            (IngestionType.OCR.value, 'OCR'),
        ],
        initial=IngestionType.NORMAL.value,
        label="Tipo di ingestione",
    )
    page_mode = forms.ChoiceField(
        choices=[
            (PageMode.SINGLE.value, 'Pagina Singola'),
            (PageMode.DOUBLE.value, 'Doppia Pagina'),
        ],
        initial=PageMode.SINGLE.value,
        label="Modalità pagina",
    )
    post_process = forms.ChoiceField(
        choices=[
            (PostProcessType.NONE.value, 'Nessuno'),
            (PostProcessType.SUMMARY.value, 'Riassunto'),
            (PostProcessType.FIX_OCR.value, 'Correzione OCR'),
            (PostProcessType.KEYWORDS.value, 'Parole chiave'),
            (PostProcessType.BOTH.value, 'Entrambi'),
        ],
        initial=PostProcessType.NONE.value,
        label="Post Processing",
        help_text="Elaborazione aggiuntiva del testo"
    )
    post_process_context = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3}),
        required=False,
        label="Contesto Post Processing",
        help_text="Fornisci informazioni aggiuntive per guidare l'elaborazione (opzionale)"
    )

    libraries = forms.MultipleChoiceField(
        choices=[],  # Will be populated in __init__
        required=False,
        label="Librerie",
        help_text="Seleziona le librerie in cui salvare il file",
        widget=forms.CheckboxSelectMultiple
    )
    
    model = File
    instance = None

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)

        self.instance = kwargs.pop("instance", None)

        super().__init__(*args, **kwargs)

        self.fields["libraries"].choices = [
            (l.library_id, l.name)
            for l in Library.objects.filter(user=self.user)
        ]
        self.fields["libraries"].help_text = (
            ""
            if Library.objects.filter(user=self.user).exists()
            else "Non hai ancora creato nessuna Libreria."
        )

        if self._is_instanced:
            self.initial["libraries"] = list(
                self.instance.libraries.values_list("library_id", flat=True)
            )
            self.fields.pop("file")

    @property
    def _is_instanced(self):
        return self.instance and self.instance.pk

    def clean_libraries(self):
        libraries_id = self.data.getlist("libraries")
        if not libraries_id:
            return Library.objects.none()
        
        return Library.objects.filter(user=self.user, library_id__in=libraries_id)
    
    def clean_file(self):
        file = self.cleaned_data.get("file")

        if file is None:
            raise forms.ValidationError("File not found.")

        if not isinstance(file, list):
            raise forms.ValidationError("File upload is not a list.")
        
        if len(file) == 0:
            raise forms.ValidationError("No file uploaded.")
        
        for f in file:
            if f is None:
                raise forms.ValidationError(f"{f} is not a valid.")
            
        return file

    def clean_ingestion_config(self):
        data = self.cleaned_data['ingestion_config']
        return IngestionConfig(**data)

    def clean(self):
        cleaned_data = super().clean()
        # Crea il modello Pydantic dalle selezioni separate
        cleaned_data['ingestion_config'] = IngestionConfig(
            type=cleaned_data.get('ingestion_type', IngestionType.NORMAL),
            mode=cleaned_data.get('page_mode', PageMode.SINGLE),
            post_process=cleaned_data.get('post_process', PostProcessType.NONE),
            post_process_context=cleaned_data.get('post_process_context')
        )
        return cleaned_data
        

    def save(self, commit=True):
        saved: List[List[bool, File, List[Library], List[Library]]] = []

        if self._is_instanced:
            uploaded, deleted = self.add_to_libraries(self.instance)
            return True, self.instance, uploaded, deleted

        files: List[InMemoryUploadedFile] = self.cleaned_data["file"]
        
        for f in files:
            file_hash = File.calculate_file_has_from_instance(f)
            possible_files = File.objects.filter(user=self.user, hash=file_hash)
            if not possible_files.exists():
                
                file_hash_norm = file_hash + os.path.splitext(f.name)[1]
                file_path: Path = settings.UPLOADS_ROOT / file_hash_norm

                counter = 1
                while file_path.exists():
                    file_path = settings.UPLOADS_ROOT / (str(counter) + file_hash_norm)
                    counter += 1

                self.save_file(f, file_path)
            
                instance = File.objects.create(
                    file=FileObject(path=file_path), 
                    user=self.user, 
                    hash=file_hash, 
                    title=f.name,
                    ingestion_config=self.cleaned_data['ingestion_config']
                )

                if commit:
                    instance.save()

                uploaded, deleted = self.add_to_libraries(instance)
                saved.append([True, instance, uploaded, deleted])
            else:
                saved.append([False, possible_files.first(), [], []])

        return saved
    
    def save_file(self, file, file_path: Path):
        """
        Funzione per salvare il file nel filesystem e restituire il suo percorso.
        Crea le directory necessarie se non esistono.
        """
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, "wb") as f:
            for chunk in file.chunks():
                f.write(chunk)
        return file_path

    def add_to_libraries(self, instance: File | None = None):
        if instance is None:
            instance = self.instance

        library_assoc = instance.libraries
        library_select = self.cleaned_data.get("libraries", Library.objects.none())
        library_utente = Library.objects.filter(user=self.user)

        libraries_to_upload = [
            library
            for library in library_utente
            if library not in library_assoc
                and library in library_select  # Non associato, ma selezionato -> upload
        ]

        libraries_to_delete = [
            library
            for library in library_utente
            if library in library_assoc
                and library not in library_select  # Associato, ma non selezionato -> elimino
        ]

        instance.assoc_library_list(libraries_to_upload)
        instance.delete_in_library_list(libraries_to_delete)

        return libraries_to_upload, libraries_to_delete
