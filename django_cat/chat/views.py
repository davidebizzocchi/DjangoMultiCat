from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DeleteView, DetailView, RedirectView

from common.mixin import LoginRequiredMixin

from django.http import Http404
from django.urls import reverse_lazy

from chat.models import Message, Chat
from chat.forms import ChatCreateForm

from icecream import ic


class ChatHome(RedirectView):
    url = reverse_lazy('chat:list')
    permanent = True


class ChatMixin():
    model = Chat
    context_object_name = "chat"

    success_url = reverse_lazy('chat:list')

    slug_url_kwarg = "chat_id"
    slug_field = "chat_id"

class ChatListView(ChatMixin, LoginRequiredMixin, ListView):
    template_name = 'chat/list.html'
    context_object_name = 'chats'

    def get_queryset(self):
        return Chat.objects.filter(user=self.usr)

class ChatStreamView(ChatMixin, LoginRequiredMixin, DetailView):
    object: "Chat"

    template_name = 'chat/streaming.html'
    context_object_name = 'thread'

    def pre_dispatch(self):
        pass

    def dispatch(self, request, *args, **kwargs):
        self.pre_dispatch()
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
    
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if isinstance(self.object, Chat):  # otherwise it's a new chat: dict
            context['chat_messages'] = Message.objects.filter(chat=self.object)
            context["agent"] = self.object.agent

        context["form"] = ChatCreateForm(user=self.usr)
        context["create_thread"] = False
        context["create_thread_immediately"] = False

        return context

class ChatCreateView(ChatStreamView):

    def get_object(self, *args, **kwargs):
        return {
            "chat_id": "new",
        }
 
    def pre_dispatch_login(self, *args, **kwargs):
        if self.request.GET.get("force", "false") == "false":
            if (qs := Chat.objects.filter(user=self.usr)).count() > 0:
                return redirect(
                    "chat:chat",
                    chat_id=qs.first().chat_id
                )
        return super().pre_dispatch_login(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["create_thread"] = True
        context["create_thread_immediately"] = False
        context["force_create_thread"] = Chat.objects.filter(user=self.usr).count() == 0

        return context

class ChatDeleteView(ChatMixin, LoginRequiredMixin, DeleteView):
    template_name = 'chat/delete_confirm.html'

