from django.urls import path, include
from chat.views import (
    home, ChatView, ChatListView, 
    ChatDeleteView, ChatCreateView
)
from chat.api import router

app_name = "chat"

urlpatterns = [
    path('', home, name='home'),
    path('list/', ChatListView.as_view(), name='list'),
    path('new/', ChatCreateView.as_view(), name='create'),
    path('<str:chat_id>/', ChatView.as_view(), name='chat'),
    path('<str:chat_id>/delete/', ChatDeleteView.as_view(), name='delete'),
]

urlpatterns.extend(router.urls_paths(""))
