from ninja import Router, File
from ninja.files import UploadedFile
from ninja.schema import Schema
from django.http import StreamingHttpResponse, JsonResponse
from chat.models import Message
import json
from icecream import ic
from cheshire_cat.client import Cat

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
    # Here you would typically:
    # 1. Save the audio file temporarily
    # 2. Use a speech-to-text service to convert it
    # 3. Return the transcribed text
    
    # For now, we'll return a dummy response
    return JsonResponse({
        "status": "success",
        "text": "This is a placeholder for the transcribed audio text."
    })
