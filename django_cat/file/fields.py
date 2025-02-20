import json
from pathlib import Path
from typing import Optional, Self
from pydantic import BaseModel, field_serializer, model_validator
from enum import Enum


class FileObject(BaseModel):
    path: Path
    size: Optional[int] = None

    class Config:
        json_encoders = {
            Path: str
        }

    def _serialize_path(self, path: Path) -> str:
        return str(path.resolve())

    @field_serializer("path")
    def serialize_path(self, path: Path):
        return self._serialize_path(path)

    @model_validator(mode="after")
    def check_size(self) -> Self:
        if self.size is None:
            self.size = self.path.stat().st_size

        return self
    
    def __str__(self):
        return self._serialize_path(self.path)
    
class FileObjectEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, FileObject):
            return obj.model_dump()
        return super().default(obj)
    
class FileObjectDecoder(json.JSONDecoder):
    def __init__(self, *args, **kwargs):
        json.JSONDecoder.__init__(self, object_hook=self.object_hook, *args, **kwargs)
    
    def object_hook(self, obj):
        if isinstance(obj, dict) and 'path' in obj:
            return FileObject(**obj)
        
        if isinstance(obj, str):
            return FileObject(path=obj)
        
        return obj

class IngestionType(str, Enum):
    NORMAL = "normal"
    OCR = "ocr"

class PageMode(str, Enum):
    SINGLE = "single"
    DOUBLE = "double"

# System prompt di base per tutti i tipi di elaborazione
SYSTEM_PROMPT = """Sei un assistente esperto in analisi e elaborazione di testi.
Il tuo compito è aiutare a processare documenti seguendo le istruzioni specifiche fornite.
Mantieni un tono professionale e fornisci output strutturati e ben organizzati.
Non aggiungere commenti personali o informazioni non richieste.
Concentrati esclusivamente sul compito assegnato.
Evita di inserire commenti, informazioni personali o spiegazioni, il risultato che fornisci verra utilizzato direttamente."""

class PostProcessType(str, Enum):
    NONE = "none"
    SUMMARY = "summary"
    FIX_OCR = "fix_ocr"
    KEYWORDS = "keywords"
    BOTH = "both"

    @property
    def prompt(self) -> str:
        """Restituisce il prompt completo includendo il system prompt"""
        task_prompt = PROCESS_PROMPTS.get(self, "")
        if (task_prompt):
            return f"{SYSTEM_PROMPT}\n\n{task_prompt}"
        return ""

# Dizionario dei prompt per ogni tipo di post-processing
PROCESS_PROMPTS = {
    PostProcessType.SUMMARY: (
        "Genera un riassunto conciso del seguente testo e formattalo come JSON nel seguente formato:\n"
        "{\n"
        '    "new_text": "il tuo riassunto qui"\n'
        "}\n\n"
        "Esempio di output:\n"
        "{\n"
        '    "new_text": "Questo è un esempio di riassunto che evidenzia i punti chiave."\n'
        "}\n\n"
        "Testo da elaborare:\n"
    ),
    PostProcessType.FIX_OCR: (
        "Correggi il seguente testo OCR e formatta il risultato come JSON nel seguente formato:\n"
        "{\n"
        '    "new_text": "il testo corretto qui"\n'
        "}\n\n"
        "Esempi di correzioni:\n\n"
        "1. Input OCR con errori di riconoscimento:\n"
        '"ll tt sa|tò sul tett0 de||a casa."\n'
        "Output corretto:\n"
        "{\n"
        '    "new_text": "Il gatto saltò sul tetto della casa."\n'
        "}\n\n"
        "2. Input OCR con problemi di formattazione:\n"
        '"Ne| |ibro si par|a di  ma te matica   e    fisica."\n'
        "Output corretto:\n"
        "{\n"
        '    "new_text": "Nel libro si parla di matematica e fisica."\n'
        "}\n\n"
        "3. Input OCR con errori di punteggiatura:\n"
        '"Disse Maria,vado a casa,sono stanca?"\n'
        "Output corretto:\n"
        "{\n"
        '    "new_text": "Disse Maria: \"Vado a casa, sono stanca.\""\n'
        "}\n\n"
        "4. Input OCR con numeri e caratteri speciali:\n"
        '"L\'anno l999 fu imp0rtante per |\'azienda N,V."\n'
        "Output corretto:\n"
        "{\n"
        '    "new_text": "L\'anno 1999 fu importante per l\'azienda N.V."\n'
        "}\n\n"
        "Testo da elaborare:\n"
    ),
    PostProcessType.KEYWORDS: (
        "Analizza il seguente testo ed estrai le parole chiave e i concetti principali. "
        "Organizza le keywords in ordine di rilevanza e raggruppa quelle correlate. "
        "Aggiungi una breve spiegazione per ogni gruppo di keywords.\n\n"
    ),
    PostProcessType.BOTH: (
        "Analizza il seguente testo ed esegui queste operazioni:\n"
        "1. Genera un riassunto conciso (circa 30% della lunghezza originale)\n"
        "2. Estrai e organizza le parole chiave in ordine di rilevanza\n"
        "3. Per ogni gruppo di keywords, fornisci una breve spiegazione\n\n"
    )
}

class IngestionConfig(BaseModel):
    type: IngestionType = IngestionType.NORMAL
    mode: PageMode = PageMode.SINGLE
    post_process: PostProcessType = PostProcessType.NONE
    post_process_context: Optional[str] = None

    def get_prompt(self) -> str:
        """Ottiene il prompt formattato con system prompt e eventuale contesto"""
        task_prompt = self.post_process.prompt
        if task_prompt:
            if self.post_process_context:
                return f"{task_prompt}\nContesto aggiuntivo: {self.post_process_context}\n\nTesto:\n"
            return task_prompt
        return ""

    @property
    def is_ocr(self) -> bool:
        return self.type == IngestionType.OCR

    @property
    def is_double_page(self) -> bool:
        return self.mode == PageMode.DOUBLE
    
    @property
    def needs_post_process(self) -> bool:
        return self.post_process != PostProcessType.NONE

class IngestionConfigEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, IngestionConfig):
            return obj.model_dump()
        return super().default(obj)

class IngestionConfigDecoder(json.JSONDecoder):
    def __init__(self, *args, **kwargs):
        json.JSONDecoder.__init__(self, object_hook=self.object_hook, *args, **kwargs)
    
    def object_hook(self, obj):
        if isinstance(obj, dict) and "type" in obj and "mode" in obj:
            return IngestionConfig(**obj)
        return obj