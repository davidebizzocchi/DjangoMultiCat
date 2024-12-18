import os
from pathlib import Path
from typing import List
from django.conf import settings
from django.core.files.uploadedfile import InMemoryUploadedFile
from django import forms
from icecream import ic

from library.models import Library
from user_upload.fields import FileObject
from user_upload.models import File


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
        
        ic("clean", result)
        return result


class FileUploadForm(forms.Form):
    file = MultipleFileField()
    libraries = forms.MultipleChoiceField(
        choices=[],
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Seleziona dove aggiungere i tuoi file",
    )

    # class Meta:
    #     model = FileUpload
    #     fields = ("file",)

    model = File
    instance = None

    def __init__(self, *args, **kwargs):
        ic.enable()
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
            else "Non hai ancora creato nessun Vector Store."
        )

        if self._is_instanced:
            self.initial["libraries"] = list(
                self.instance.libraries.values_list("library_id", flat=True)
            )
            self.fields.pop("file")

        ic("init")

    @property
    def _is_instanced(self):
        return self.instance and self.instance.pk

    def clean_vects(self):
        libraries_id = self.data.getlist("vects")
        if not libraries_id:
            return Library.objects.none()
        
        ic("clean vects", libraries_id)
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
        

    def save(self, commit=True):
        ic(self._is_instanced)
        saved: List[List[bool, File, List[Library], List[Library]]] = []  # bool = True -> created / False -> not created, first VectorStore add / secondo Vectorstore delete

        if self._is_instanced:
            uploaded, deleted = self.add_to_libraries(self.instance)
            saved.append([True, self.instance, uploaded, deleted])
            return saved

        files: List[InMemoryUploadedFile] = self.cleaned_data["file"]
        
        ic(files)

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

                ic(file_hash_norm, file_path)

                self.save_file(f, file_path)
            
                instance = File.objects.create(
                    file=FileObject(path=file_path), user=self.user, hash=file_hash, title=f.name
                )

                if commit:
                    instance.save()

                uploaded, deleted = self.add_to_libraries(instance)
                saved.append([True, instance, uploaded, deleted])

            else:
                ic("Il file esiste già!")
                saved.append([False, possible_files.first(), [], []])

        return saved
    
    def save_file(self, file, file_path):
        """
        Funzione per salvare il file nel filesystem e restituire il suo percorso.
        """
        
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
            for library in library_assoc
            if library not in library_utente
                and library in library_select  # Non associato, ma selezionato -> upload
        ]

        libraries_to_delete = [
            library
            for library in library_utente
            if library in library_assoc
                and library not in library_select  # Associato, ma non selezionato -> elimino
        ]

        instance.upload_in_library_list(libraries_to_upload)
        instance.delete_in_library_list(libraries_to_delete)

        return libraries_to_upload, libraries_to_delete
