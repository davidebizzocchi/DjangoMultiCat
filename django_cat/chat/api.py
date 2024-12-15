from ninja import Router, File
from ninja.files import UploadedFile
from ninja.schema import Schema
from django.http import StreamingHttpResponse, JsonResponse, FileResponse
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

class TextIn(Schema):
    text: str

router = Router()

def get_user_client(user) -> Cat:
    return user.userprofile.client

def message_generator(message, usr):
    client: Cat = get_user_client(usr)

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

    # Get user's client
    client: Cat = get_user_client(request.user)
    
    # Get transcription
    transcribed_text = client.transcribe(audio.file)
    
    return JsonResponse({
        "status": "success",
        "text": transcribed_text,
        # "file": filename
    })

@router.post("/speak-api", url_name="speak-api")
def speak(request, data: TextIn):
    client: Cat = get_user_client(request.user)
    audio_stream = client.speak(data.text)
    
    response = FileResponse(
        audio_stream,
        content_type='audio/mp3',
        as_attachment=False,
        filename='speech.mp3'
    )
    return response

@router.get("/speak-last-api", url_name="speak-last-api")
def speak_last(request):
    # Get last assistant message using optimized query
    last_message = Message.get_last_assistant_message(request.user)
    
    if not last_message:
        return JsonResponse({
            "status": "error",
            "message": "No messages found"
        }, status=404)

    client: Cat = get_user_client(request.user)
    audio_stream = client.speak(last_message.text)
    
    response = FileResponse(
        audio_stream,
        content_type='audio/mp3',
        as_attachment=False,
        filename='speech.mp3'
    )
    return response
