from ninja import Router, File
from ninja.files import UploadedFile
from ninja.schema import Schema
from django.http import StreamingHttpResponse, JsonResponse
from chat.models import Message
import json
from icecream import ic
from cheshire_cat.client import Cat
from django.conf import settings
import os
from pathlib import Path
import glob

class MessageIn(Schema):
    message: str

router = Router()

def message_generator(message, usr):
    client: Cat = usr.userprofile.client

    # response_text = ""
    # # Simulate character by character processing
    # for char in message:
    #     response_text += char
    #     yield f"data: {json.dumps({'data': char})}\n\n"

    client.send(message)
    for token in client.stream():
        yield f"data: {json.dumps({'data': token.content})}\n\n"
    
    # Save assistant response
    Message.objects.create(
        user=usr,
        text=client.wait_message_content().content,
        sender=Message.Sender.ASSISTANT
    )
    
    yield "event: done\ndata: {}\n\n"

@router.post("/stream-api", url_name="stream-api")
def stream(request, data: MessageIn):
    # Save user message
    Message.objects.create(
        user=request.user,
        text=data.message,
        sender=Message.Sender.USER
    )

    response = StreamingHttpResponse(
        message_generator(data.message, request.user),
        content_type='text/event-stream'
    )
    response['Cache-Control'] = 'no-cache'
    response['X-Accel-Buffering'] = 'no'
    return response

@router.post("/audio-api", url_name="audio-api")
def audio_upload(request, audio: UploadedFile = File(...)):
    # # Create audio directory if it doesn't exist
    # audio_dir = settings.MEDIA_ROOT / "audio"
    # audio_dir.mkdir(parents=True, exist_ok=True)
    
    # Get user's client
    client = request.user.userprofile.client
    
    # Get transcription
    transcribed_text = client.transcribe(audio.file)
    
    # # Get user's cheshire_cat ID and save file
    # cheshire_id = request.user.userprofile.cheschire_id
    
    # # # Find next available number for this user
    # # pattern = str(audio_dir / f"{cheshire_id}_*.wav")
    # # existing_files = glob.glob(pattern)
    # # next_number = len(existing_files) + 1
    
    # # # Create filename and save
    # filename = f"{cheshire_id}_{next_number}.wav"
    # filepath = audio_dir / filename
    
    # with open(filepath, "wb+") as destination:
    #     audio.file.seek(0)  # Reset file pointer
    #     for chunk in audio.chunks():
    #         destination.write(chunk)
            
    # print(f"Saved audio file: {filepath}")
    
    return JsonResponse({
        "status": "success",
        "text": transcribed_text,
        # "file": filename
    })
