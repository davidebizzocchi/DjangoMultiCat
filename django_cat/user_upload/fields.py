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

class IngestionConfig(BaseModel):
    type: IngestionType = IngestionType.NORMAL
    mode: PageMode = PageMode.SINGLE

    @property
    def is_ocr(self) -> bool:
        return self.type == IngestionType.OCR

    @property
    def is_double_page(self) -> bool:
        return self.mode == PageMode.DOUBLE

    # Rimuovi get_choices() visto che ora gestiamo le scelte nel form

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