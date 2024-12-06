from django.shortcuts import render
from django.views.generic import TemplateView

from chat.models import Message

def home(request):
    return render(request, 'chat/home.html')

class ChatView(TemplateView):
    template_name = 'chat/streaming.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['chat_messages'] = Message.objects.filter(user=self.request.user)
        return context