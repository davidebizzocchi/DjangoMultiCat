from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import TemplateView, ListView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.urls import reverse_lazy
from django.views.generic.edit import FormView

from chat.models import Message, Chat
from chat.forms import ChatCreateForm

def home(request):
    return render(request, 'chat/home.html')

class ChatListView(LoginRequiredMixin, ListView):
    model = Chat
    template_name = 'chat/list.html'
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
        context['chat_id'] = chat.chat_id  # Add this line
        return context

class ChatCreateView(LoginRequiredMixin, FormView):
    template_name = 'chat/new.html'
    form_class = ChatCreateForm
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        chat = Chat.objects.create(user=self.request.user)
        # Here you can handle the selected libraries
        # This will be used later for chat context
        libraries = form.cleaned_data['libraries']
        if libraries:
            chat.libraries.set(libraries)

            for library in chat.libraries.all():
                library.add_new_chat(str(chat.chat_id))
        return redirect('chat:chat', chat_id=chat.chat_id)

# Remove or comment out the old create_chat function
# @login_required
# def create_chat(request):
#     ...

class ChatDeleteView(LoginRequiredMixin, DeleteView):
    model = Chat
    template_name = 'chat/delete_confirm.html'
    success_url = reverse_lazy('chat:list')
    context_object_name = 'chat'
    
    def get_object(self, queryset=None):
        chat = get_object_or_404(Chat, chat_id=self.kwargs['chat_id'])
        if chat.user != self.request.user:
            raise Http404("Chat non trovata")
        return chat
