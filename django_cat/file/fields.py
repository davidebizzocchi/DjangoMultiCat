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
    AUDIO = "audio"

class PageMode(str, Enum):
    SINGLE = "single"
    DOUBLE = "double"

# System prompt di base per tutti i tipi di elaborazione
SYSTEM_PROMPT = """You are an expert assistant in text analysis and processing.
Your task is to help process documents following specific instructions.
Maintain a professional tone and provide structured, well-organized output.
Do not add personal comments or unrequested information.
Focus exclusively on the assigned task.
Avoid including comments, personal information or explanations, your output will be used directly."""

class PostProcessType(str, Enum):
    NONE = "none"
    SUMMARY = "summary"
    FIX_OCR = "fix_ocr"
    AUDIO = "audio"
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
        "Generate a concise summary of the following text and format it as JSON in the following format:\n"
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
        "Fix the following OCR text and format the result as JSON in the following format:\n"
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
    PostProcessType.AUDIO: (
        "Clean and format the following audio transcription text as Markdown, then return as JSON in this format:\n"
        "```json\n"
        "{\n"
        '    "new_text": "formatted markdown text here"\n'
        "}\n"
        "```\n\n"
        "**Audio transcription corrections should include:**\n"
        "- Remove filler words (uh, um, like)\n"
        "- Fix false starts and repetitions\n"
        "- Add proper punctuation\n"
        "- Capitalize properly\n"
        "- Format numbers and dates consistently\n"
        "- Apply Markdown formatting for:\n"
        "  - Headers (`#`, `##`)\n"
        "  - Lists (`-` or `1.`)\n"
        "  - Emphasis (`*italic*`, `**bold**`)\n"
        "  - Quotes (`> `)\n"
        "  - Code (`` ` `` or ``` ```)\n\n"
        "**Examples:**\n\n"
        "1. Raw transcription with speech artifacts:\n"
        "```\n"
        '"uh i was thinking maybe we could um meet at 3 pm on tuesday for the *important* project"\n'
        "```\n"
        "Cleaned Markdown version:\n"
        "```json\n"
        "{\n"
        '    "new_text": "I was thinking we could meet at 3:00 PM on Tuesday for the **important** project."\n'
        "}\n"
        "```\n\n"
        "2. Meeting notes transcription:\n"
        "```\n"
        '"ok so first item uh infrastructure costs second security updates third q3 goals"\n'
        "```\n"
        "Formatted as Markdown list:\n"
        "```json\n"
        "{\n"
        '    "new_text": "## Meeting Notes\\n\\n- Infrastructure costs\\n- Security updates\\n- Q3 goals"\n'
        "}\n"
        "```\n\n"
        "3. Technical discussion:\n"
        "```\n"
        '"we need to use the json module like this import json data equals json dot loads string"\n'
        "```\n"
        "With code formatting:\n"
        "```json\n"
        "{\n"
        '    "new_text": "We need to use the `json` module like this: `import json\\ndata = json.loads(string)`"\n'
        "}\n"
        "```\n\n"
        "Text to process:\n"
    ),
    PostProcessType.KEYWORDS: (
        "Analyze the following text and extract key words and main concepts. "
        "Organize keywords by relevance and group related ones. "
        "Add a brief explanation for each group of keywords.\n\n"
    ),
    PostProcessType.BOTH: (
        "Analyze the following text and perform these operations:\n"
        "1. Generate a concise summary (about 30% of original length)\n"
        "2. Extract and organize keywords by relevance\n"
        "3. For each group of keywords, provide a brief explanation\n\n"
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
    def is_audio(self) -> bool:
        return self.type == IngestionType.AUDIO

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