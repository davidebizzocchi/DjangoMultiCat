from typing import List, Optional, Union
from django.urls import reverse
from ninja import Router, File
from ninja.files import UploadedFile
from ninja.schema import Schema
from django.http import StreamingHttpResponse, JsonResponse, FileResponse
from chat.models import Chat, Message
import json
from icecream import ic
from cheshire_cat.client import Cat
from django.shortcuts import get_object_or_404
from agent.models import Agent
from library.models import Library

router = Router(tags=["Chat"])

class MessageIn(Schema):
    message: str
    chat_id: str

class TextIn(Schema):
    text: str

# MiniThreadSchema now represents a Chat summary; 'title' is managed via an optional attribute on Chat
class MiniThreadSchema(Schema):
    thread_id: str
    title: str
    date: str

class MessageStreamPayloadSchema(Schema):
    message: str

class LimitValueSchema(Schema):
    limit: int = 100

class StartLimitValueSchemaSchema(Schema):
    limit: int = 10
    start: int = 0

class ThreadValueSchema(Schema):
    thread_id: str

class RenameValueSchema(Schema):
    name: str
    thread_id: str

class ThreadCreateSchema(Schema):
    name: Optional[str] = None
    agent: str = "default"
    libraries: Optional[Union[List[str], str]] = None


def get_user_client(user) -> Cat:
    return user.userprofile.client

def message_generator(message, chat, user):
    """Generator function that streams messages from a specific chat"""

    # Retrive Chat models instance
    if isinstance(chat, str):
        chat = get_object_or_404(Chat, chat_id=chat, user=user)
    elif not isinstance(chat, Chat):
        raise ValueError("Invalid chat type")
    
    # Retrive message text
    if isinstance(message, Message):
        message = message.text
    elif not isinstance(message, str):
        raise ValueError("Invalid message type")
    
    # Send message using chat
    chat.send_message(message)
    
    # Stream responses from specific chat
    for token in chat.stream():
        yield f"data: {json.dumps({'data': token.text})}\n\n"
    
    # Save assistant response
    Message.objects.create(
        text=chat.wait_message_content().text,  
        sender=Message.Sender.ASSISTANT,
        chat=chat
    )
    
    yield "event: Done\ndata: {}\n\n"

@router.post("/stream-api", url_name="stream-api")
def stream(request, data: MessageIn):
    # Save user message
    chat = get_object_or_404(Chat, chat_id=data.chat_id, user=request.user)
    Message.objects.create(
        text=data.message,
        sender=Message.Sender.USER,
        chat=chat
    )

    response = StreamingHttpResponse(
        message_generator(data.message, data.chat_id, request.user),
        content_type='text/event-stream'
    )
    response['Cache-Control'] = 'no-cache'
    response['X-Accel-Buffering'] = 'no'
    return response

@router.post("/audio-api", url_name="audio-api")
def audio_upload(request, audio: UploadedFile = File(...)):
    client: Cat = get_user_client(request.user)
    
    # Get transcription
    transcribed_text = client.transcribe(audio.file)
    
    return JsonResponse({
        "status": "success",
        "text": transcribed_text
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

@router.get("/speak-last-api/{chat_id}", url_name="speak-last-api")
def speak_last(request, chat_id: str):
    # Get chat and verify ownership
    chat = get_object_or_404(Chat, chat_id=chat_id, user=request.user)
    
    # Get last assistant message for this specific chat
    last_message = Message.objects.filter(
        chat=chat,
        sender=Message.Sender.ASSISTANT
    ).order_by('-timestamp').first()
    
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

@router.post("/wipe-chat/{chat_id}", url_name="wipe-chat-api")
def wipe_chat(request, chat_id: str):
    # Get chat and verify ownership  
    chat = get_object_or_404(Chat, chat_id=chat_id, user=request.user)
    
    # Wipe chat memory
    chat.wipe()
    
    # Delete all messages from database
    Message.objects.filter(chat=chat).delete()
    
    return JsonResponse({
        "status": "success",
        "message": "Chat memory wiped successfully"
    })

@router.delete("threads/{thread_id}/", response=dict, url_name="thread-delete")
def thread_delete(request, thread_id: str):

    chat = get_object_or_404(Chat, chat_id=thread_id, user=request.user)
    chat.delete()
    return {"success": True}

@router.put("threads/{thread_id}/rename", response=dict, url_name="thread-rename")
def thread_rename(request, thread_id: str, name: str):
    chat = get_object_or_404(Chat, chat_id=thread_id, user=request.user)

    chat.title = name
    chat.save()
    return {"success": True}

@router.post("threads/list", response=List[MiniThreadSchema], url_name="thread-list")
def thread_list(request, data: StartLimitValueSchemaSchema) -> List[MiniThreadSchema]:
    chats = Chat.objects.filter(user=request.user)[data.start : data.start + data.limit]

    return [
        MiniThreadSchema(
            thread_id=chat.chat_id,
            title=chat.name,
            date=chat.timedelta
        ) 
        for chat in chats
    ]

@router.post("messages/{thread_id}/list", response=dict, url_name="message-list")
def message_list(request, thread_id: str, data: LimitValueSchema):
    limit = data.limit
    chat = get_object_or_404(Chat, chat_id=thread_id, user=request.user)
    messages_qs = chat.messages.only("text", "timestamp", "sender")
    messages = messages_qs if limit == 0 else messages_qs[:limit]

    return {
        "thread_id": thread_id,
        "messages": [
            {
                "text": m.text,
                "timestamp": m.timestamp.isoformat(),
                "sender": m.sender,
            }
            for m in messages
        ]
    }

@router.post("threads/{thread_id}/stream", url_name="thread-stream")
def stream_response(request, thread_id: str, payload: MessageStreamPayloadSchema):
    message = payload.message

    chat = get_object_or_404(Chat, chat_id=thread_id, user=request.user)

    Message.objects.create(
        text=message,
        sender=Message.Sender.USER,
        chat=chat
    )

    response = StreamingHttpResponse(
        message_generator(message, chat, request.user),
        content_type="text/event-stream"
    )
    response['Cache-Control'] = 'no-cache'
    response['X-Accel-Buffering'] = 'no'
    return response

@router.post("threads/thread-url", response=dict, url_name="thread-url")
def get_thread_url(request, data: ThreadValueSchema):
    chat = get_object_or_404(Chat, chat_id=data.thread_id, user=request.user)

    return {
        "url": reverse("chat:chat", kwargs={"chat_id": chat.chat_id}),
    }

@router.post("threads/create", url_name="thread-create")
def create_thread(request, data: ThreadCreateSchema):
    ic("create_thread", data)
    user = request.user

    if data.agent == "default":
        agent = Agent.get_default()
    else:
        agent = Agent.objects.get(agent_id=data.agent, user=user)

    chat = Chat.objects.create(user=user, agent=agent)

    if data.name is not None:
        chat.title = data.name
        chat.save()
        
    if data.libraries is not None:
        if isinstance(data.libraries, str):
            data.libraries = [data.libraries]
            
        for library in Library.objects.only("id").filter(library_id__in=data.libraries, user=user):
            chat.libraries.add(library)
            library.add_new_chat(str(chat.chat_id))

        chat.save()

    return JsonResponse({
        "thread_id": chat.chat_id,
        "success": True,
        "url": reverse("chat:chat", kwargs={"chat_id": chat.chat_id})
        })