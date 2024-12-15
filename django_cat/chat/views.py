from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import TemplateView, ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.urls import reverse

from chat.models import Message, Chat

def home(request):
    return render(request, 'chat/home.html')

class ChatListView(LoginRequiredMixin, ListView):
    model = Chat
    template_name = 'chat/chat_list.html'
    context_object_name = 'chats'

    def get_queryset(self):
        return Chat.objects.filter(user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Aggiungi il primo messaggio per ogni chat come titolo
        chat_titles = {}
        for chat in context['chats']:
            first_message = chat.messages.first()
            chat_titles[chat.id] = first_message.text[:50] if first_message else "Nuova Chat"
        context['chat_titles'] = chat_titles
        return context

class ChatView(LoginRequiredMixin, TemplateView):
    template_name = 'chat/streaming.html'
    
    def get(self, request, *args, **kwargs):
        chat = get_object_or_404(Chat, chat_id=kwargs['chat_id'])
        if chat.user != request.user:
            raise Http404("Chat non trovata")
        return super().get(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        chat = get_object_or_404(Chat, chat_id=kwargs['chat_id'])
        context['chat'] = chat
        context['chat_messages'] = Message.objects.filter(chat=chat)
        return context

@login_required
def create_chat(request):
    if request.method == 'POST':
        chat = Chat.objects.create(user=request.user)
        return redirect('chat:chat_detail', chat_id=chat.chat_id)
    return redirect('chat:chat_list')

@login_required
def delete_chat(request, chat_id):
    if request.method == 'POST':
        chat = get_object_or_404(Chat, chat_id=chat_id, user=request.user)
        chat.delete()
    return redirect('chat:chat_list')