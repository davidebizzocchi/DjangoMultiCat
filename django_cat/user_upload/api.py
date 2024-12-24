from ninja import Router, Schema
from django.shortcuts import get_object_or_404
from user_upload.models import File
from typing import Optional

router = Router()

class FileStatusSchema(Schema):
    status: str
    progress: int
    is_ocr: bool
    is_ingested: bool

@router.get("/{file_id}/status", response=FileStatusSchema, url_name="config_status")
def get_file_status(request, file_id: str):
    file = get_object_or_404(File, file_id=file_id, user=request.user)
    return {
        "status": file.status,
        "progress": file.config_progress,
        "is_ocr": file.ingestion_config.is_ocr,
        "is_ingested": file.ingested
    }
