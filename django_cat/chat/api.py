from ninja import Router
from ninja.schema import Schema
from django.http import StreamingHttpResponse
from chat.models import Message
import json
from icecream import ic

class MessageIn(Schema):
    message: str

router = Router()

def message_generator(message, user):
    response_text = ""
    # Simulate character by character processing
    for char in message:
        response_text += char
        yield f"data: {json.dumps({'data': char})}\n\n"
    
    # Save assistant response
    Message.objects.create(
        user=user,
        text=response_text,
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
