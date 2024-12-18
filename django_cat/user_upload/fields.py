import json
from pathlib import Path
from typing import Optional, Self
from pydantic import BaseModel, field_serializer, model_validator


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